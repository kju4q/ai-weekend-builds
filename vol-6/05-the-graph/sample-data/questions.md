# Sample questions and expected answers

Invented. Used by `ask.py --eval` in milestone M4 of the spec.

## 1. Which of my projects came from something I read by Mira Okafor?
- Expected entities: Tiny model, Auditor
- Expected files: projects/tiny-model/README.md, projects/auditor/README.md
- Why it is a graph question: the auditor README names only "The Second Reader". Reaching Okafor needs the merge of "M. Okafor" and "Okafor" and the edge from that piece to its author.

## 2. What idea links my router to a talk I watched?
- Expected entities: routing by task type, Theo Lindqvist, "Spend Less on Inference"
- Expected files: projects/router/README.md, notes/2026-05-routing.md

## 3. Which idea did I hold that something I read disagrees with?
- Expected entities: always using the biggest model, routing by task type
- Expected files: notes/2026-05-routing.md

## 4. Which sources are about independent review, and who wrote them?
- Expected entities: "The Second Reader", Mira Okafor
- Expected files: reading/okafor-second-reader.md, notes/2026-08-review.md

## 5. Which ideas does the tiny model use, and where did I first read about them?
- Expected entities: next-token prediction, cross-entropy loss, "Small Models, Honest Loss"
- Expected files: projects/tiny-model/README.md, reading/okafor-small-models.md
