# Example pack

This directory is a **self-contained demonstration** of LastLight. It exists so somebody landing on the repository can run the project immediately without first finding an external knowledge pack.

The committed ZIP is intentionally tiny and combines several unrelated emergency topics only to demonstrate retrieval, language routing, provenance, refusal and source attribution. It is **not** an official LastLight knowledge release and should not be treated as a substitute for current local authorities or primary guidance.

The long-term project direction remains unchanged: real packs should live and evolve in a separate `lastlight-packs` repository, a future `lastlight-hub` should make them easy to discover/download, and companion tools/UI should stay in their own repositories.

## Included artifact

```text
lastlight-example-es.zip
├── lastlight-pack.json
├── README.md
└── es/
    ├── agua/potabilizacion.md
    ├── apagon/alimentos.md
    └── primeros-auxilios/sangrado-grave.md
```

The same source files are kept under [`source/`](source/) so the ZIP can be inspected without extracting it.

## Try it

```bash
python src/main.py --knowledge examplepack/lastlight-example-es.zip --validate-pack
python src/main.py --knowledge examplepack/lastlight-example-es.zip --verify-provenance
python src/main.py --knowledge examplepack/lastlight-example-es.zip "¿cómo hago segura el agua?"
```

SHA-256 of the committed ZIP:

```text
3c2422409207636ae945830861036ef93019c52ef7b2741b54338376778ce48e
```
