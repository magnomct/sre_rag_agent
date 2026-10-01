"""
SRE RAG Agent — Knowledge Indexer Module
Loads, chunks, embeds and indexes SRE documentation (Runbooks, Postmortems, Architecture).
"""

import os
import re
import json
import glob
import math
import structlog
from typing import Optional
from pathlib import Path

logger = structlog.get_logger()


class DocumentChunk:
    def __init__(
        self,
        id: str,
        title: str,
        source: str,
        category: str,
        section: str,
        content: str,
        metadata: Optional[dict] = None,
        embedding: Optional[list[float]] = None,
    ):
        self.id = id
        self.title = title
        self.source = source
        self.category = category
        self.section = section
        self.content = content
        self.metadata = metadata or {}
        self.embedding = embedding

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "category": self.category,
            "section": self.section,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentChunk":
        return cls(
            id=data["id"],
            title=data["title"],
            source=data["source"],
            category=data["category"],
            section=data["section"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
        )


class SREKnowledgeIndexer:
    """
    Manages indexing and vector search over the SRE documentation corpus.
    """

    def __init__(
        self,
        docs_dir: Optional[str] = None,
        index_file: Optional[str] = None,
    ):
        base_app_dir = Path(__file__).resolve().parent.parent
        repo_root = base_app_dir.parent

        self.docs_dir = Path(docs_dir) if docs_dir else repo_root / "docs"
        self.index_file = (
            Path(index_file)
            if index_file
            else base_app_dir / "rag" / "index_store.json"
        )
        self.chunks: list[DocumentChunk] = []
        self._is_indexed = False

    def _determine_category(self, filepath: Path) -> str:
        rel = filepath.relative_to(self.docs_dir).as_posix()
        if rel.startswith("runbooks/"):
            return "runbook"
        elif rel.startswith("postmortems/"):
            return "postmortem"
        elif "slo" in rel.lower():
            return "slo"
        elif "incident" in rel.lower():
            return "incident_response"
        elif "architecture" in rel.lower():
            return "architecture"
        return "general"

    def _extract_document_title(self, content: str, filename: str) -> str:
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return filename.replace(".md", "").replace("-", " ").title()

    def parse_markdown_to_chunks(self, filepath: Path) -> list[DocumentChunk]:
        """
        Parses a markdown file into semantic chunks grouped by sections (## / ###).
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_content = f.read()
        except Exception as e:
            logger.error("read_doc_failed", file=str(filepath), error=str(e))
            return []

        doc_title = self._extract_document_title(raw_content, filepath.name)
        category = self._determine_category(filepath)
        rel_source = str(filepath.name)

        # Split content by markdown section headings
        section_pattern = re.compile(r"^(#{1,3}\s+.*)$", re.MULTILINE)
        splits = section_pattern.split(raw_content)

        chunks: list[DocumentChunk] = []
        current_section = "Overview"
        chunk_seq = 0

        i = 0
        while i < len(splits):
            part = splits[i].strip()
            if not part:
                i += 1
                continue

            if part.startswith("#"):
                current_section = part.lstrip("#").strip()
                # Next part contains the body for this heading
                if i + 1 < len(splits):
                    body = splits[i + 1].strip()
                    i += 1
                else:
                    body = ""
            else:
                body = part

            if len(body) > 30:  # Ignore trivial snippets
                chunk_seq += 1
                chunk_id = f"{filepath.stem}-{chunk_seq}"
                full_text = f"[{doc_title} > {current_section}]\n{body}"

                chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        title=doc_title,
                        source=f"docs/{category}s/{filepath.name}" if category in ["runbook", "postmortem"] else f"docs/{filepath.name}",
                        category=category,
                        section=current_section,
                        content=full_text,
                        metadata={
                            "filename": filepath.name,
                            "section": current_section,
                            "length": len(full_text),
                        },
                    )
                )
            i += 1

        return chunks

    def load_all_chunks(self) -> list[DocumentChunk]:
        """Scans docs directory and returns all parsed chunks."""
        all_chunks: list[DocumentChunk] = []

        patterns = [
            self.docs_dir / "runbooks" / "*.md",
            self.docs_dir / "postmortems" / "*.md",
            self.docs_dir / "architecture.md",
            self.docs_dir / "slo.md",
            self.docs_dir / "incident-response.md",
        ]

        files_to_index: list[Path] = []
        for pat in patterns:
            files_to_index.extend(sorted(glob.glob(str(pat))))

        # Deduplicate & filter
        seen = set()
        for f in files_to_index:
            p = Path(f)
            if p.is_file() and p not in seen and not p.name.endswith("-template.md"):
                seen.add(p)
                chunks = self.parse_markdown_to_chunks(p)
                all_chunks.extend(chunks)

        logger.info(
            "corpus_chunks_parsed",
            files_scanned=len(seen),
            total_chunks=len(all_chunks),
        )
        return all_chunks

    def build_index(self, force: bool = False):
        """
        Builds the vector index. If index_file exists and not force, loads it.
        Otherwise encodes all chunks using sentence-transformers and saves to disk.
        """
        if self._is_indexed and not force:
            return

        if self.index_file.exists() and not force:
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.chunks = [DocumentChunk.from_dict(d) for d in data.get("chunks", [])]
                self._is_indexed = True
                logger.info("index_loaded_from_disk", chunks_count=len(self.chunks), file=str(self.index_file))
                return
            except Exception as e:
                logger.warning("failed_loading_cached_index", error=str(e))

        logger.info("building_fresh_vector_index", docs_dir=str(self.docs_dir))
        self.chunks = self.load_all_chunks()

        if not self.chunks:
            logger.warning("no_documents_found_to_index")
            self._is_indexed = True
            return

        # Generate embeddings in batch
        from rag.embeddings import generate_embeddings

        texts = [chunk.content for chunk in self.chunks]
        embeddings = generate_embeddings(texts)

        for chunk, emb in zip(self.chunks, embeddings):
            # Normalize vector for cosine similarity
            norm = math.sqrt(sum(x * x for x in emb)) or 1.0
            chunk.embedding = [x / norm for x in emb]

        # Save to disk
        try:
            self.index_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "total_chunks": len(self.chunks),
                        "chunks": [c.to_dict() for c in self.chunks],
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            logger.info("index_saved_to_disk", chunks_saved=len(self.chunks), path=str(self.index_file))
        except Exception as e:
            logger.error("save_index_error", error=str(e))

        self._is_indexed = True

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        min_score: float = 0.15,
    ) -> list[dict]:
        """
        Searches the vector index using cosine similarity.
        """
        if not self._is_indexed:
            self.build_index()

        if not self.chunks:
            return []

        # Normalize query vector
        norm = math.sqrt(sum(x * x for x in query_embedding)) or 1.0
        norm_query = [x / norm for x in query_embedding]

        scored_chunks: list[tuple[float, DocumentChunk]] = []

        for chunk in self.chunks:
            if not chunk.embedding:
                continue
            # Cosine similarity via dot product of unit vectors
            score = sum(q * d for q, d in zip(norm_query, chunk.embedding))
            if score >= min_score:
                scored_chunks.append((score, chunk))

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk in scored_chunks[:top_k]:
            results.append(
                {
                    "id": chunk.id,
                    "title": chunk.title,
                    "content": chunk.content,
                    "source": chunk.source,
                    "category": chunk.category,
                    "section": chunk.section,
                    "score": round(score, 4),
                    "metadata": chunk.metadata,
                }
            )

        return results

    def search_by_text(self, query: str, top_k: int = 3) -> list[dict]:
        from rag.embeddings import generate_query_embedding

        emb = generate_query_embedding(query)
        return self.search(emb, top_k=top_k)


# Singleton indexer instance
sre_indexer = SREKnowledgeIndexer()
