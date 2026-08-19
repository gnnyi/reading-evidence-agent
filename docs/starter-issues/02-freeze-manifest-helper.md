# Starter: make benchmark freeze manifests reproducible without running a model

## Why

The frozen adversarial review already hashes Gold and sorted corpus files, but that logic lives inside the review runner. A future blind benchmark needs a small dependency-free way to create or verify a freeze manifest *before* any candidate system is run.

## Fixture

Use a temporary directory containing:

```text
corpus/
  a.md
  nested/b.md
gold.json
```

Run the proposed helper twice with different `PYTHONHASHSEED` values. Then modify one corpus byte and, separately, one Gold byte.

## Expected result

- repeated runs over unchanged inputs produce byte-identical manifest JSON;
- the manifest includes a format/version marker, Gold SHA-256, and an aggregate hash derived from sorted relative corpus paths plus each file SHA-256;
- changing corpus bytes changes the corpus aggregate hash;
- changing Gold changes the Gold hash;
- the helper performs no retrieval, classification, model call, or network access;
- it does not silently overwrite an existing freeze unless explicitly requested.

## Acceptance test

Add unit tests for byte stability, path-order stability, corpus tamper detection, Gold tamper detection, and overwrite protection. Reuse one shared hashing implementation from the review runner rather than creating two subtly different freeze contracts.
