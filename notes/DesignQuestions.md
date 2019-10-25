# Design Questions
* Cross-modal ranking, as a loss function suggested in project proposal, tries to output small values for text-image pairs
of the same article, while big values - for mismathing values. But often articles are similar and desribing similar concept and
even referencing the same images. While other are indeed completely different. Should we enhance loss function to acknowledge existance
of different similiarities between different articles?
