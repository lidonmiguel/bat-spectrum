## Research Position and Limitations

I am not a biologist, nor an expert in bioacoustics or bat sound identification. Because of that, this project does not attempt to make definitive scientific interpretations of the recordings, the species, or the biological meaning of the detected calls.

My position in this project is closer to that of an interested amateur, artist, and developer exploring how bat recordings can be analysed and transformed into a visual system.

What I have been able to observe is that it is possible to detect bat-like acoustic events in ultrasonic recordings and translate their measurable qualities into a visual constellation map. Each detected pulse can become a node, and the relationships between pulses can become connections. This makes it easier to observe aspects of the sound such as timing, frequency, energy, density, and variation.

The resulting visual map is not a replacement for scientific analysis. Instead, it is a way to make acoustic structure visible and readable. It offers a different way of approaching the recordings: not as a final biological classification, but as an audiovisual interpretation of their sonic qualities.

With a larger and cleaner dataset, recorded with the same device and under consistent conditions, this project could move closer to a scientific study. For now, it remains a visual and computational exploration — perhaps scientific enough to be interesting, and not scientific enough to annoy a biologist too much.


## Noise, Data Quality, and Cleaning

Many of the recordings I have been able to work with come from the generous work of biologists, recordists, and people who document these species in the field. Field recordings are often imperfect. They can include camera handling noise, human movement, wind, environmental sounds, or other unwanted acoustic material.

For anyone working with data, it is clear how important clean data is. A noisy recording can affect interpretation, detection, and visualization.

Because of this, I created an additional script that can generate a cleaned version of the current audio. This script does not modify the original recording. Instead, it creates a derived file that focuses on the parts of the audio that are more likely to contain bat calls, using frequency filtering and pulse-based masking.

However, for the main visual workflow, I have not treated the cleaned audio as the primary source XD. The original recording remains the reference material. In many cases, the analysis script already ignores a large amount of irrelevant noise because it focuses on specific frequency ranges and pulse-like acoustic events.

The cleaning script is therefore best understood as a support tool: useful for listening, reviewing, and testing, but not a replacement for the original data.

## Interpretation

The visual outputs in Bat Spectrum should be understood as acoustic maps, not biological conclusions.

They can help reveal patterns in the recordings, but they do not prove species identity, behaviour, or ecological meaning on their own.

This project is an exploration of how computational analysis and visual design can make hidden ultrasonic structures more accessible, while still respecting the limits of my own knowledge and the complexity of bat bioacoustics.
