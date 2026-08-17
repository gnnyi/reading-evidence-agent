# Privacy boundary

This repository contains only code, documentation, and newly authored synthetic demo material.

## Never commit

- raw exports from reading platforms;
- real user highlights or personal questions;
- account-specific source identifiers;
- journals, messages, annotations, or private gold labels;
- generated embeddings, local indexes, or raw benchmark output;
- absolute filesystem paths, credentials, environment files, or sensitive traces.

Removing a name is not sufficient anonymization. Real personal questions and real reading excerpts remain private even if obvious identifiers are deleted.

## Safe public material

- generic engine and schema code;
- synthetic notes, questions, and relation labels written for this demo;
- reproducible tests and metrics;
- generic failure taxonomies and architecture decisions.

## Local benchmark rule

Private evaluation is opt-in through explicit CLI paths. The CLI does not discover private data, and it writes nothing into the repository unless the operator explicitly chooses a repository path. The default generated index directory is ignored by Git.

Before any remote publication, review tracked files, scan staged content for credentials and private markers, and inspect the full Git history—not only the working tree.
