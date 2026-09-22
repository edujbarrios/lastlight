# Example pack

This directory is a **self-contained English-first demonstration** of LastLight. It exists so somebody landing on the repository can run the project immediately without first finding an external knowledge pack.

The committed ZIP is intentionally tiny and combines several unrelated emergency topics only to demonstrate retrieval, language routing, provenance, refusal and source attribution. It is **not** an official LastLight knowledge release and should not be treated as a substitute for current local authorities or primary guidance.

The long-term project direction remains unchanged: real packs should live and evolve in a separate `lastlight-packs` repository, a future `lastlight-hub` should make them easy to discover/download, and companion tools/UI should stay in their own repositories.

## Included artifact

```text
lastlight-example-en.zip
├── lastlight-pack.json
├── README.md
└── en/
    ├── water/purification.md
    ├── blackout/food-safety.md
    └── first-aid/severe-bleeding.md
```

The same source files are kept under [`source/`](source/) so the ZIP can be inspected without extracting it.

## Try it

```bash
python src/main.py --knowledge examplepack/lastlight-example-en.zip --validate-pack
python src/main.py --knowledge examplepack/lastlight-example-en.zip --verify-provenance
python src/main.py --knowledge examplepack/lastlight-example-en.zip "The water supply is down and I have no bottled water. I found water that looks clear. What should I do before drinking it?"
```

SHA-256 of the committed ZIP:

```text
18ec0065f47bfeee7f1df5caeb5b3944d08f555edd497d551ba653d451c5f4f8
```
