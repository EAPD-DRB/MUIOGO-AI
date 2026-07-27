# Scientific basis and limits

There is no single peer-reviewed OSeMOSYS/CLEWs accreditation test that declares a country model “correctly calibrated.” The rubric operationalizes recurring principles from energy-system modeling, model evaluation, and CLEWs/OSeMOSYS practice.

## Core sources

- DeCarolis et al. (2017), “Formalizing best practice for energy system optimization modelling,” *Applied Energy* 194, 184–198. DOI: https://doi.org/10.1016/j.apenergy.2017.03.001
  Supports iterative calibration against historical trends, model verification, uncertainty analysis, transparency, and fitness of model features to the research question.

- Howells et al. (2011), “OSeMOSYS: The Open Source Energy Modeling System,” *Energy Policy* 39(10), 5850–5870. DOI: https://doi.org/10.1016/j.enpol.2011.06.033
  Establishes the OSeMOSYS framework and its transparent, open modeling rationale.

- Prina et al. (2023), “The state of macro-energy systems research: Common critiques, current progress, and research priorities,” *Renewable and Sustainable Energy Reviews* / open-access record: https://pmc.ncbi.nlm.nih.gov/articles/PMC10040701/
  Distinguishes validation from broader model evaluation and discusses historical backcasting, uncertainty, transparency, physical constraints, and applicability.

- Plazas-Niño (2024), “Model Calibration – Power Sector,” Advanced Energy System Modelling Using OSeMOSYS, Zenodo. https://doi.org/10.5281/zenodo.10854698
  Provides OSeMOSYS-specific capacity and generation calibration practice.

- Barnes et al. (2022), “OSeMOSYS Global, an open-source, open data global electricity system model generator,” *Scientific Data* 9. https://doi.org/10.1038/s41597-022-01737-0
  Demonstrates transparent model generation, historical country comparisons, and geographic sensitivity as a validation aid.

- Shchiptsova et al. (2016), “Assessing historical reliability of the agent-based model of the global energy system,” *Journal of Systems Science and Systems Engineering* 25, 326–350. DOI: https://doi.org/10.1007/s11518-016-5303-7
  Provides a formal example of comparing historical observations and model outputs as a distance and analyzing calibration uncertainty.

## Methodological interpretation

The following are reasoned extensions, not claims that every source mandates the exact thresholds:

- the E/J/H forcing classes;
- the 0–100 weights and grade boundaries;
- the history-fixed percentage caps;
- domain score floors;
- the five-grade classification.

They make reviewer judgments explicit and repeatable. Projects should preregister or adapt tolerances and weights to their policy context, then document changes. Do not tune the rubric after seeing which grade a favored model receives.

## Terminology caution

“Backcasting” is used inconsistently. Here, **historical simulation or hindcasting** means initializing the model at an earlier historical state and testing it against later observations not used for tuning. It does not mean normative sustainability backcasting from a desired future.
