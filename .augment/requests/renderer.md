
# Project Context

## Processing Strategy

I need you to recall this information to your context: 
- This is the current strategy that we are following (on `strategy_v2.0.md`) the schemas and specifics of the implementation and design decisions are a little bit outdated, but the general strategy is still valid, which is: 
  - Root Branch 0 - Raw Transcription (cannonical text from whisper)
  - [Processing before Branches ]
    - Whisper deliver words with timestamps. 
    - We are using `segment-any-text/sat-12l-sm` to produce a segmentation of the text ("pieces"), semantically meaningful chunks of text, which became the "canonical" unit of text for further processing.
    - From the SAT model we are getting only the segmented text, so we are running a post-processing step to assign timestamps to each piece, by looking at the timestamps of the words that compose the piece, and assigning the timestamps of the first and last word to the piece (like saying "from here to there").
  - Branch A - Hierarchical titles: 
    - The only change introduced from Branch 0, is that we are interleaving the paragraphs breaks and the ierarchical titles to the transcription, which will be used for better navigation and organization of the content. But the transcription itself is not changed, we are not doing any cleaning or formatting, just interleaving the titles and paragraphs breaks.
    - This branch return a markdown with the organized transcription. (implemented and working)
  - Branch B - Semantic Reorganization:
    - Still no cleaning or formatting. 
    - The goal of this branch is to tackle the following problem described in this common issue: "During a conference or class, the spekaker may jump between topics, and the transcription may not be organized in a way that reflects the structure of the content. This can make it difficult for users to navigate and understand the material."
    - The goal of this branch is to reorganize the transcription in a way that reflects the structure of the content, by grouping the pieces into semantically meaningful sections, and generating a meaningful title for each section.
    - This uses `BAAI/bge-m3` to generate embeddings for the pieces, and then uses a k-means clustering algorithm to group the pieces into clusters. 
    - This branch return Clusters of pieces, which share a common theme or topic, and a title that summarizes the topic of the cluster (implemented and partially working)
  - Branch C - Grounded Summarization (Condensed, Traceable, Formatted and cleaned):
    - The goal of this branch is to produce a condensed, traceable, formatted and cleaned summary of the content, which can be used for quick reference and review.
    - The key value of this branch is that the summary is grounded, meaning that each piece of information in the summary is traceable to the original transcription pieces, and from there, to the original audio timestamps **and this is the key insight for this chat in particular**.

## Processing Deliverables to the User. 

- Root Branch 0 - Raw Transcription => Raw Text file with the verbatim transcription of the audio, without timestamps, not organized in any way, just the text as it is transcribed by whisper.
- Branch A - Hierarchical titles => Markdown file with the transcription organized with hierarchical titles and paragraphs breaks. 
- Branch B - Semantic Reorganization => 
  - Still not defined how it will be delivered to the user. 
  - Currently, we are generating a JSON file with the clusters of pieces, pieces timestamps, and their cluster titles. 
- Branch C - Grounded Summarization => Markdown file with the grounded summary of the content.
  - Not implemented yet. 
  - The idea is to generate an structured hierarchical summary in a markdown file, where each piece of information in the summary is traceable to the original transcription pieces (through cites with their ids), and from there, to the original audio timestamps.

# Resources available 

## .zip file

- In the .zip file you will find a collection of .json files, each one corresponding to an intermediate processing step of the processing strategy. 
- The goal of this files is to provide you with the objects and data structures that we are using in the different steps of the processing strategy, so you can understand which elements are available for the implementation of the renderer, and how to use them.
- The files are named with this convention: 
  - across all files, the "sample0x" files correspond to the same audio, where x is a number that identifies the audio file. 
  - across all files, the "sample0x_<process-name>_y" files correspond to variations of the same processing step (mainly different due different LLM responses), where y is a letter (a, b, c,) that identifies the variation.
- The directories are specified as follows: 
```bash
# Here Rx corresponds to the Root Branch (R) processing steps, Ax corresponds to the Branch A processing steps, and Bx corresponds to the Branch B processing steps
    .data/
    ├── a1_tittle_tree/             # A1 (Branch A) - Raw return from the Qwen model with the hierarchical titles and paragraphs breaks (the "content" key)
    ├── a2_recompose_md/            # A2 (Branch A) - Markdown file with the transcription organized with hierarchical titles and paragraphs breaks. 
    ├── b1_clusters/                # B1 (Branch B) - Intermediate outputs of the branch up to the clusters and tentative markdown output.   
    ├── sample0x_p03_bundle_y/          # Branch B processing from this cannon bundle  
    │   ├── stage1_out/                     # Intermediate outputs
    │   ├── stage2_out/                     # Intermediate outputs 
    │   ├── stage3_out/                     # Intermediate outputs
    │   ├── stage4_out/                     # Intermediate outputs
    │   ├── stage5_out/                     # Clusters JSON reports
    │   └── stage6_out/                     # Tentative markdown output
    ├── n06_whisper/                # R1. Whisper output with words and timestamps
    ├── p02_split_SaT/              # R2. SAT segmentation of the text into "pieces"
    └── p03_build_cannon_bundle/    # R3. Post-processing step to assign timestamps to the pieces, building the "cannon bundle" (pieces with their text and timestamps)
```

## FastAPI + Jinja2 + HTMX  Web App => intended for Google Cloud Run Environment 

- In particular, since the B branch required heavy python processing that was not able to be handled by the n8n cloud instance, we moved that part to a Google Cloud Run environment.
- For that reason we implemented a "minimal, production-friendly FastAPI + Jinja2 + HTMX" app that was intended to enable just the API, but **it was also great and easy to implemement a simple UI to interact with it**. 
- The `minimal_production_firednly_fastAPI_jinja2_htmx.md` attached doc provides what was your suggestion about how to implement it. 
  - Pay attention to the structure, level of granularity of the information and quality of the code snippets. 


# Current Task

## Goal

The goal of this task is to implement a web renderer for the output of the processing strategy described in the `strategy_v2.0.md` document. 
As was comented in prior chat interactions, all the branches what they provide are "views" from the same data with different levels of fidelity to summarization, all traceable, so apart from the documents, the goal will be to provide a web app that allows the user to navigate across with zero friction. 

**Key Pain**: The current UI-like are markdown documents whith the traceability encoded in cites interleaved within the document. This approach, although solves the traceability by providing the information, is not user friendly in any way, since the user would need to constantly switch between documents and actual json to achieve the full trace, which became quickly a pain.




**Envisioned solution**: 
The ideal solution that I'm tinkering with is the following: 
- When opening a transcribed document, the user will open by default the organized transcription (branch A) which will be presented apparently at face value, with the view fully designed to be easy to read and study. Apparently it would show nothing more ( like quotes, links, etc.)
- The key advantage of the view appears when the user "hover" over the text. 
  - In that moment, the view will subtletly highlight the whole "piece" at which belong the hovered word. 

- The hovering behavior it's the same on both views (Branch A and Branch C), but the information that is shown in the tooltip is different: 
  - In Branch A, the tooltip will show the init and end timestamp of the piece, and a link to open the audio at that timestamp. 
    - If the user clicks on the link, the audio will open as a transparent overlay on the bottom of the document, and it will start playing from the timestamp of the piece, while highlighting the "piece" in real time as they are being pronounced in the audio.
  - In Branch C, the tooltip will show the list of pieces that are cited in the summary sentence. 
    - If the user clicks on one of the pieces, another tab will open with the original structured transcription (Branch A), and it will jump to the piece in the transcription, where the user can hover and click to listen to the audio as explained in the previous point.


- Also, for both Branch A & Branch C views, in the upper left cornet will appear a "show clusters" button, that will add subtle colors to the highlights of the pieces, encoding according to their cluster belonging (from Branch B), so the user can have a visual aid to identify which pieces belong to the same cluster and share a common theme or topic. Important clarification, the color is added to the highlits, so its only showed when the user hovers over the piece.
  - When pressing the "show clusters" button, a panel overlay will deploy under the button, showing the title of the cluster. 
  - If hovering over cluster title, all the belonging pieces will be higlihgted with the corresponding color of the cluster title.
  - If clicked on the cluster title, the highlight will be on state always visible, and if clicked again it will return to the only hovering higlight. 
  - Multiple cluster title could be clicked simultaneously as to show how the topics interleave. 


- Also the hovering behavior itself can be toggled on/off by the user, disabling it entirely in case they prefer a more "clean" view without the hovering highlights and tooltips, or configured if the user wants to have the highlights with or without cluster colors, or with or without the tooltips, or if they want to change the cluster color (double click on the title shows a set of available colors to choose, just a predefined group of colors)

- The idea is to provide a seamless navigation between the summary and the original transcription, and between the transcription and the audio, allowing the user to easily access the original content and context of each piece of information in the summary.
- And give a visual aid about the topics discussed and how they are related. 

**Other Aspects of the Web App**: 
- On the left panel, it would show a personal directory with the transcriptions added by the user. It can add folders and it has a search bar. 
- Above the view, it will be always buttons to move from one view to another (audio, transcription, summary)
- Also it should be able to create an user account with a google account (or just email & password), that would enable multiple users to get access to its own documents. 

**Later Addendums** :
- Later on the following features would be implemented: 
  - Button to add a new audio => it would send the audio to the pipeline, and return the new doc fully processed ready to view. 
  - Sync with google drive folder: 
    - If detects an audio in the folder, it automatically starts the processing and return a directory with the name of the audio containing the transcription, the summary and the clusters. 


## TASK (this is the only things you need to do know): 

1. Review available alternatives on Google Cloud Run or Google Cloud VM (or any other alternative available on the web that would be suitable for this project) BE COMPREHENSIVE AND THOROUGH ON THIS SEARCH THIS IS KEY FOR THE SUCCESS OF THE PROJECT PROOF OF CONCEPT. 
2. Provide a tier list of the options (VM vs Cloud Run / Serverless, keep on Google or change of provier) BE COMPREHENSIVE AND THOROUGH ON THIS SEARCH THIS IS KEY FOR THE SUCCESS OF THE PROJECT PROOF OF CONCEPT. 
   1. **The KEY CRITERIA is to be able to be able to run the project under the free tier of the provider** since we are in the process of getting the Proof of concept.
   2. ALSO it should be **ideal** but not a deal-breaker to be able to push the project via github or another similar alternative, so it would be easier to implement locally. 
3. Provide a tier list of the stack alternatives existent to run this project FastAPI/Jinja2/HTMX ? the older LAMP stack?
   1. **The KEY CRITERIA here is to use an stack that allow EASY AND QUICK DEVELOPMENT FOR FULL PROOF OF CONCEPT**, while also balancing with the scalability that the complexity of the project requires. 
   2. Incorporate in the assessment, maturity, flexibility, maintainability, toolset available (boiler-plate generators, no-code generators, and any other tool that would aim to achieve the goal of **PoF quick and easy, even if not beautiful** => Later this project will be funded to be properly implemented. The goal now is to have something working. ) 
4. A report on the **minimal production friendly architecture** following your best recommendations for the implementation.
   1. Follow the same level of detail than the `minimal_production_friednly_fastAPI_jinja2_htmx.md`, but extend it in order to cover every that's needed. 
   2. Make sure to identify and follow a modular approach since this project probably would need to be implemented on sections. 
      1. Make sure that the modules defines clear and precise contracts for it's communication, with the goal of decouple the implementation of the modules, under the premise that "if the contract is follow precisely the integration should be seamessly.  
      2. The report should have a clear set of plantUML diagram that show the architecture and the communication between the modules, recursively. Meaning: 
         1. High level diagram with high level modules and the contracts in between them. 
         2. Then for each high level module, a new diagram with the internal modules and it's contracts. 
         3. And so for each module. Use as many layers of recursiveness as needed for a clear architecture explanation. 

## DELIVERABLES: 
- Thorough tier list with the infrastructure alternatives, a clear recommendation and why the others were not chosen. 
- Thorough tier list with the alternatives stacks, a clear recommendation and why the others were not chosen. 
- An extensive report in markdown detailing **minimal production friendly architecture** following your best recommendations for the implementation.