# Design Questions
* Cross-modal ranking, as a loss function suggested in project proposal, tries to output small values for text-image pairs
of the same article, while big values - for mismathing values. But often articles are similar and desribing similar concept and
even referencing the same images. While other are indeed completely different. Should we enhance loss function to acknowledge existance
of different similiarities between different articles?


# Design Approach
* In [Word2VisualVec](https://www.researchgate.net/profile/Xirong_Li2/publication/301648180_Word2VisualVec_Cross-Media_Retrieval_by_Visual_Feature_Prediction/links/575f728c08ae414b8e549902/Word2VisualVec-Cross-Media-Retrieval-by-Visual-Feature-Prediction.pdf) the get general image features as target variable (e.g. output of some of the internal fully-connected layers of ImageNet trained CNN). Then they train CNN to match between vectorised text as input and corresponding image features as target variable.
  * Then in our case we can do similarly be defining loss function not with single image, but as sum of similiaroties of N images divided by N. Is it theoretically good model? (although, it's easier to implement than original one and it's also coordinated learning).
  * With this approach should we really map text equally for all images? Could some images be far more specific for that text and other general for a lot of articles? If we map equally, probably, we need to properly process images and remove comm
