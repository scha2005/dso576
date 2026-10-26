# Project Starting Point

## Team and GitHub

| Team name | GitHub repository |
|---|---|
| PyForce | https://github.com/scha2005/dso576.git |

## Selected project area

AI in the workforce

## Why our team is interested in it

As AI is reshaping the workplace, our team is interested in which roles should incorporate AI into their workflow to improve efficiency. Also, we are interested in what AI-related skills are necessary for each different sector.

## Candidate Vision A

A career seeker using a university career center must decide which career path to pursue by comparing different job opportunities, considering their long-term career prospects, and evaluating how likely each occupation is to be affected or potentially replaced by AI and automation in the future.

## Candidate Vision B

A business strategist at a company looking to integrate AI must decide how and where to incorporate AI into workflows, which positions need to receive extra training, and how to make sure that the company receives the most ROI from AI incorporation by looking at trends of AI use in various roles.

## Side-by-side candidate assessment

| Assessment | Vision A | Vision B |
|---|---|---|
| Evidence found so far |The Anthropic Economic Index dataset connects real-world Claude usage with O*NET tasks and occupations. Its occupation- and task-level measures can help career seekers compare how AI is currently used across different career paths, including whether AI tends to automate tasks or augment human work.| The Economic Index includes job-exposure and task-penetration data that can be used to construct a relative AI-exposure score for different occupations. Anthropic’s labor-market impact study also introduces an observed-exposure measure based on AI capabilities and real-world, work-related AI usage.|
| Core-data fit | Partial — The core data can support comparisons of AI exposure and task-level change across occupations, but it does not include all the information needed for a career decision, such as personal interests, education costs, location, salary preferences, and complete long-term employment prospects.| Partial — The core data can support occupation comparisons, relative exposure estimates, and a transparent risk-ranking system. However, it cannot independently predict with certainty whether or when a specific occupation will be replaced, nor can it define the “best” occupation without additional criteria.|
| Biggest risk |Users may interpret high AI exposure as evidence that an occupation will disappear, even though exposure may instead mean that AI will change or assist some tasks within the occupation. The results could also be incomplete if important personal and labor-market factors are excluded.| A predictive score or ranking may appear more certain than the underlying evidence supports. Results may also depend heavily on how “AI risk” and “best job” are defined, weighted, and communicated to users.|

## Core data source we confirmed we can access

Anthropic Economic Index, https://huggingface.co/datasets/Anthropic/EconomicIndex, It opened up a link to Anthropic’s analysis of AI impact on the US economy.

## Three questions we still need to resolve

1. How should we systematically map O*NET occupation codes in the Anthropic dataset to normalized salary and employment growth data from the BLS (Bureau of Labor Statistics) to evaluate true career viability alongside AI exposure?
2. How can we mathematically distinguish between AI task automation (replacing human tasks) and AI task augmentation (enhancing productivity) within the dataset to avoid misleading users into thinking high AI exposure equals job loss?
3. What auxiliary data sources or weighting methodologies should we implement to account for regional demand variations and non-technical job requirements such as soft skills or physical presence that AI usage logs cannot capture?

## Role-file progress

Use one of these status labels: **Not started**, **In progress**, **Ready for team review**, **Complete**, or **Not applicable**.

| Role file | Owner | Status |
|---|---|---|
| [`objectives.md`](objectives.md) | Sumedha | In progress |
| [`alternatives.md`](alternatives.md) | Jade | Not started |
| [`data-fit.md`](data-fit.md) | Keya | In progress |
| [`auxiliary.md`](auxiliary.md) | Allen | Not started |
| [`technical.md`](technical.md) | Ella | Not started |
| [`objections.md`](objections.md) | [Name or GitHub username] | Not applicable |

## Team check

- [Y] We added our team name and the correct private GitHub repository link.
- [Y] We selected the area based first on genuine team interest.
- [Y] A and B are distinct candidate Visions within the same area.
- [Y] The candidate comparison uses verified evidence rather than unsupported claims.
- [Y] At least one data source opened, or we recorded the access blocker.
- [Y] We preserved three real questions instead of hiding uncertainty.
- [Y] Every active role file has an owner and a current status.
- [Y] Every teammate reviewed this provisional starting point.
