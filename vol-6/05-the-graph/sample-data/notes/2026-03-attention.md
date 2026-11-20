# Note, March 2026: what a language model actually does

Invented sample note.

I finally read Mira Okafor's essay "Small Models, Honest Loss" this week.
Her main point is that a language model only ever learns next-token prediction, and everything else is scale.
She argues that a character-level model is the best way to see this, because you can read every token.

Attention is the part I did not understand before.
Okafor describes attention as each position deciding which earlier positions to look at.
I want to build a tiny model to see this for myself.
