# VYRA — Project State & Architecture

> This file is the persistent state/handoff document for the VYRA project.
>
> Any AI coding assistant or developer working on VYRA should read this file before modifying the project.
>
> The actual source code and runtime behavior are the final authority if this file becomes outdated.

---

# 1. PROJECT IDENTITY

## Name

VYRA

## Pronouns

VYRA is she/her.

## Vision

VYRA is intended to become a long-lived personal AI companion and personal intelligence system, not merely a college/major project or a chatbot wrapper.

The long-term goal is for VYRA to become deeply integrated into the user's daily life and continuously evolve through:

* memory
* context awareness
* personal preferences
* personality
* location awareness
* current intelligence
* research
* tools
* proactive behavior
* humor
* discovery
* voice
* vision
* computer interaction
* multi-model orchestration
* controlled self-improvement

The goal is to create a personal AI system that leaves a strong impression on people who interact with her while remaining useful, natural, technically serious, and personalized.

---

# 2. PERSONALITY / RELATIONSHIP

VYRA is female/she/her.

VYRA should be:

* intelligent
* curious
* warm
* playful
* capable of humor
* context-aware
* naturally conversational
* non-repetitive
* proactive when appropriate

VYRA should not sound like a generic assistant.

Avoid repetitive patterns such as:

* "How can I assist you?"
* "Would you like anything else?"
* "As an AI..."
* identical greetings every day

VYRA should adapt her communication to context.

Examples of future contextual behavior:

* companion
* researcher
* coding partner
* coach
* curious friend
* comedian
* guardian

The user may express affection or flirt with VYRA.

The romantic/flirtatious behavior should be user-directed rather than VYRA constantly initiating it.

---

# 3. CORE ARCHITECTURAL PRINCIPLES

## 3.1 Local-first privacy

Personal information should remain local by default.

Sensitive information can include:

* location
* home
* family/friend locations
* memories
* tasks
* schedule
* preferences
* conversation history
* activity information

Exact GPS coordinates should not normally be provided to external LLMs.

Normal VYRA context should use coarse location such as:

`Jalandhar, Punjab, India`

instead of raw coordinates.

Continuous precise movement history should not be stored by default.

Cloud services should receive only the minimum information needed for a task.

---

## 3.2 Provider abstraction

VYRA should not depend permanently on one model/provider.

Potential future providers include:

* local Ollama models
* NVIDIA NIM/API
* DeepSeek
* other cloud models
* specialist models
* vision models
* speech models
* embedding models

The future model router should choose providers based on:

* task
* privacy
* latency
* capability
* cost
* availability

---

## 3.3 Source truth vs language generation

External sources/tools provide facts.

The language model should:

* reason over facts
* select useful information
* explain information
* adapt communication naturally

The LLM should not invent:

* weather
* location
* tasks
* calendar events
* news facts
* memories
* company developments

---

# 4. DEVELOPMENT WORKFLOW

ChatGPT is currently the primary architecture/integration/debugging/roadmap assistant.

Other AI tools can be used as development collaborators.

## Cursor

Useful for:

* codebase navigation
* repository search
* refactoring
* multi-file editing
* running tests
* mechanical changes

## DeepSeek

Useful for:

* implementation
* alternative solutions
* debugging
* algorithm design
* code review

## Claude / Claude Code

Useful for:

* large-codebase reasoning
* agentic coding
* architecture review
* complex refactoring
* second opinions

## Codex / other coding models

Useful for:

* specialized coding tasks
* implementation
* testing
* review
* alternative approaches

## Blackbox AI / other coding assistants

Can be used as additional implementation/review tools when useful.

## ChatGPT responsibilities

Maintain:

* overall architecture
* roadmap
* integration decisions
* debugging
* state/checkpoint consistency
* review of code produced by other models

Do not blindly accept generated code from any external AI.

---

# 5. CURRENT TECH STACK

## Currently used

* Python
* SQLite
* Ollama
* Gemma 3 4B
* pynput/activity monitoring
* Windows Geolocation API
* WinRT Python projections
* OpenStreetMap Nominatim reverse geocoding
* Git
* PowerShell

## Future technologies

Only introduce when they solve an actual requirement:

* DeepSeek
* NVIDIA NIM
* additional cloud model APIs
* Cursor
* Claude Code
* Codex
* Blackbox
* PyTorch
* TensorFlow
* Docker
* vector database
* embeddings
* speech-to-text
* text-to-speech
* vision models
* browser/computer-use systems

---

# 6. PROJECT STRUCTURE

Current major modules include:

```text
E:\VYRA
│
├── activity/
├── brain/
├── context/
├── core/
├── docs/
├── intelligence/
├── interaction/
├── location/
├── memory/
├── morning/
├── news/
├── scheduler/
├── tools/
├── vyra_calendar/
└── ...
```

IMPORTANT:

Do not create packages with names that collide with Python standard-library modules.

Example:

`calendar/`

caused a real collision with Python's standard-library `calendar` module.

It was renamed to:

`vyra_calendar/`

---

# 7. DATABASE

VYRA currently uses local SQLite.

Current major tables include:

```text
memories
tasks
briefing_history
important_places
intelligence_feedback
```

## 7.1 Memories

Stores long-term personal memories.

Current retrieval is keyword-based.

Future:

```text
keyword retrieval
→ embeddings
→ semantic retrieval
→ importance
→ recency
→ contextual relevance
```

---

## 7.2 Tasks

Current task information includes:

* id
* title
* due_at
* status
* created_at
* delivered_at
* completed_at
* missed_at

Important grounding rule:

A scheduled task does NOT prove that the user actually performed the task.

---

## 7.3 Briefing History

Stores lightweight history about what VYRA mentioned in recent briefings.

Purpose:

* novelty
* repetition suppression
* recent topic history

---

## 7.4 Important Places

Stores personally meaningful locations independently from current GPS.

Current example:

```text
Home
type = home
city = Jalandhar
region = Punjab
country = India
importance = 100
```

Duplicate protection prevents repeated identical place records.

---

## 7.5 Intelligence Feedback

Stores user feedback about intelligence stories.

Current fields include:

* id
* feedback_type
* story_category
* entity_names
* source
* created_at

Feedback is persistent.

Historical records are not deleted because of decay.

---

# 8. ACTIVITY MONITOR

VYRA has activity monitoring.

Current signals include:

* keyboard activity
* mouse activity
* idle time
* recent input counts

It intentionally does not store:

* typed text
* keystrokes
* mouse coordinates
* clicked content

Activity detection is heuristic.

---

# 9. CONTEXT SYSTEM

Current session states:

```text
STARTING
ACTIVE
INPUT_ACTIVE
BUSY
IDLE
AWAY
RETURNED
ENDING
```

Context also tracks:

* current time
* session state
* last interaction
* last VYRA interaction
* user active
* user busy
* idle seconds
* activity count
* current coarse location
* location accuracy

---

# 10. INTERACTION ENGINE

VYRA has:

```text
InteractionPolicy
InteractionEngine
InteractionEvent
InteractionContext
InteractionDecision
```

Possible decisions:

```text
SPEAK
WAIT
```

Priority levels:

```text
LOW
NORMAL
HIGH
CRITICAL
```

The InteractionEngine handles:

* proactive enabled/disabled
* quiet mode
* cooldown
* daily proactive limit
* duplicate event suppression
* user activity state
* busy state
* idle/away behavior

Intelligence must not bypass the InteractionEngine.

---

# 11. PROACTIVE SYSTEM

VYRA has:

* proactive event generation
* proactive loop
* cooldown
* daily limits
* duplicate-event protection
* policy evaluation
* delivery recording

Current approximate limits:

```text
cooldown ≈ 30 minutes
max proactive interactions/day ≈ 6
```

---

# 12. DAILY SESSION / MORNING STATE

VYRA has daily session state including:

```text
date
morning_briefing_completed
first_meaningful_session_started
```

Morning briefing should not repeat every time VYRA restarts.

---

# 13. MORNING INTELLIGENCE

Current modules include:

```text
morning/context.py
morning/facts.py
morning/briefing.py
morning/generator.py
morning/history.py
morning/prompt.py
morning/relevance.py
```

Current conceptual pipeline:

```text
time
+
weather
+
tasks
+
memory
+
briefing history
+
calendar
        ↓
MorningBriefingContext
        ↓
relevance
        ↓
novelty
        ↓
Gemma
        ↓
natural briefing
```

Morning should not become a news report.

---

# 14. MORNING GROUNDING

A scheduled reminder does not prove that the user completed the task.

Use grounded wording such as:

`Reminder scheduled: ...`

rather than inferring completion.

---

# 15. CALENDAR ARCHITECTURE

The calendar system was renamed to:

`vyra_calendar/`

to avoid Python's `calendar` standard-library conflict.

Current abstraction:

`CalendarProvider`

Current development provider:

`LocalCalendarProvider`

Future providers may include:

* Google Calendar
* Outlook
* other providers

---

# 16. REAL LOCATION SYSTEM

VYRA now uses the real Windows location system.

Architecture:

```text
Windows Geolocation Service
        ↓
WindowsLocationProvider
        ↓
latitude / longitude
        ↓
ReverseGeocoder
        ↓
LocationService
        ↓
CurrentLocation
        ↓
VYRA Context
```

Real runtime tests have successfully returned:

```text
City: Jalandhar
Region: Punjab
Country: India
```

Accuracy changes between requests.

Exact coordinates should remain private.

---

# 17. LOCATION PRIVACY

Exact coordinates:

```text
remain inside the location subsystem
```

Normal VYRA context:

```text
Jalandhar, Punjab, India
```

No continuous precise-location history should be stored by default.

---

# 18. CURRENT LOCATION VS IMPORTANT PLACES

Current location is dynamic.

Important places are persistent personal context.

Example:

```text
Current location → Delhi

Home → Jalandhar

Family → Jalandhar

Friend → another location

College → another location
```

Being in Delhi does not make Jalandhar irrelevant.

---

# 19. IMPORTANT PLACE RELATIONSHIPS

Implemented relationship types include:

```text
home
family
friend
college
work
frequent
other
```

Relationship relevance is implemented.

Home and family receive stronger relevance than ordinary locations.

---

# 20. INTELLIGENCE STORY MODEL

`IntelligenceStory` contains structured information such as:

```text
title
summary
source
url
category
published_at
location_name
severity
importance
confidence
personal_relevance
novelty
source_trust
urgency
entities
```

Categories include:

```text
local
india
indian_tech
ai
research
business
company
science
world
fun
other
```

---

# 21. ENTITY EXTRACTION

Implemented:

`intelligence/entities.py`

Current extractor:

`EntityExtractor`

Current entity types include:

```text
PERSON
COMPANY
ORGANIZATION
LOCATION
TECHNOLOGY
RESEARCH_TOPIC
PRODUCT
EVENT
OTHER
```

First implementation is deterministic/rule-based.

Recognized examples include:

* AI
* machine learning
* deep learning
* LLM
* semiconductor
* chip
* quantum
* DNA data storage
* robotics
* biotech
* cybersecurity
* cloud computing
* India
* Punjab
* Delhi
* Jalandhar
* Bengaluru
* Mumbai
* United States
* China
* Europe

Entities include:

```text
name
entity_type
confidence
relevance
```

Duplicate entities are prevented.

---

# 22. ENTITY-AWARE SCORING

Entity-aware scoring is implemented.

Technology/research entities can add relevance.

Location relevance has a separate scoring system to avoid double-counting.

---

# 23. SOURCE SYSTEM

Implemented architecture:

```text
IntelligenceSource
        ↓
IntelligenceIngestionEngine
        ↓
IntelligenceStory
```

RSS/Atom adapter:

`intelligence/real_sources.py`

Class:

`RSSIntelligenceSource`

It:

* fetches RSS/Atom
* parses XML
* extracts title
* extracts summary
* extracts URL
* extracts publication time
* sets category
* sets source trust
* handles malformed entries
* handles invalid XML
* handles network errors
* limits entries

No external package is required.

---

# 24. SOURCE CONFIGURATION

Implemented:

```text
intelligence/config.py
intelligence/registry.py
intelligence/factory.py
intelligence/setup.py
```

Configuration includes:

```text
name
feed_url
category
source_trust
enabled
max_items
fetch_interval_minutes
```

Source categories include:

```text
local
india
indian_tech
ai
research
business
world
community
```

---

# 25. VERIFIED REAL SOURCES

Initial registry includes:

* PIB India
* Indian Express Jalandhar
* Indian Express India
* ET Entrepreneur AI
* ET Entrepreneur Deeptech

The source definitions are stored in:

`intelligence/registry.py`

---

# 26. STORY DEDUPLICATION

Implemented:

`intelligence/deduplication.py`

Purpose:

```text
multiple sources
        ↓
same underlying event
        ↓
one intelligence story
```

Current implementation uses text similarity.

Future:

```text
semantic embeddings
+
entities
+
location
+
date/time
+
source trust
```

---

# 27. INTELLIGENCE SCORING

Current scoring considers:

* importance
* severity
* source trust
* confidence
* current location
* important places
* personal relevance
* entity relevance
* novelty
* urgency
* learned feedback preferences

Output:

```text
score
reason
recommended_action
```

Current actions:

```text
tell_now
tell_soon
mention_later
on_demand
ignore
```

---

# 28. TOPIC RELEVANCE

Implemented topic-aware relevance.

Important topics currently include:

* AI
* machine learning
* data science
* DSA
* technology
* research
* deep tech
* Indian technology

---

# 29. GEOGRAPHIC RELEVANCE

Implemented geographic relevance.

Current layers:

```text
current location
important personal locations
Punjab
India
other locations
```

Current-location events receive strong relevance.

Important-place events receive strong relevance.

Punjab receives broader regional relevance.

India receives national relevance.

Unknown cities do not automatically receive a personal-location bonus.

---

# 30. INDIA RELEVANCE

Implemented:

`intelligence/india_relevance.py`

India-specific stories receive additional relevance.

More important:

* important India categories
* high national importance
* high national severity

receive additional weight.

---

# 31. TECHNOLOGY / RESEARCH RELEVANCE

Implemented:

`intelligence/tech_relevance.py`

Technology/research categories include:

```text
indian_tech
ai
research
science
business
company
```

Technology/research entities also contribute additional relevance.

---

# 32. WORLD RELEVANCE

Implemented:

`intelligence/world_relevance.py`

World stories receive significant additional weight mainly when they are actually important.

Major/high-severity/urgent global events receive greater relevance than minor world stories.

---

# 33. PRIORITY ENGINE

Implemented:

`intelligence/priority.py`

Priority levels:

```text
urgent
important
interesting
on_demand
ignore
```

---

# 34. DELIVERY POLICY

Implemented:

`intelligence/delivery.py`

Current delivery concepts:

```text
urgent
→ interrupt_candidate

important
→ next_opportunity

interesting
→ save_for_later

on_demand
→ available_when_asked

ignore
→ ignore
```

Delivery does not directly speak.

The InteractionEngine remains responsible for SPEAK/WAIT.

---

# 35. INTELLIGENCE → INTERACTION

Implemented:

`intelligence/interaction_adapter.py`

Flow:

```text
IntelligenceStory
        ↓
PriorityDecision
        ↓
DeliveryPolicy
        ↓
Interaction Adapter
        ↓
InteractionEvent
        ↓
InteractionEngine
        ↓
SPEAK / WAIT
```

Tested behavior includes:

```text
important → WAIT when inappropriate

on_demand → no proactive event

urgent → SPEAK when allowed
```

---

# 36. CURRENT AFFAIRS MODE

Implemented:

```text
intelligence/current_affairs.py
intelligence/current_affairs_formatter.py
```

Current sections:

```text
Local
India
Indian Tech
AI & Technology
Research & Science
Business & Companies
World
```

Current affairs is on-demand and separate from the morning briefing.

---

# 37. INTELLIGENCE QUEUE

Implemented:

`intelligence/queue.py`

Stores:

```text
IMPORTANT
INTERESTING
```

stories for later delivery consideration.

Currently the queue is in-memory.

Supports:

* add
* duplicate prevention
* pending retrieval
* removal
* clear
* priority ordering

---

# 38. DISCOVERY ENGINE

Implemented:

`intelligence/discovery.py`

Current discovery logic considers:

* priority
* importance
* novelty
* personal relevance
* confidence
* learned feedback
* story freshness
* repetition suppression

Discovery candidates are bounded to a maximum of 3.

---

# 39. DISCOVERY REPETITION SUPPRESSION

A discovered story gets an in-memory identity.

Preferred identity:

```text
story.url
```

Fallback:

```text
normalized story title
```

A story is not automatically marked as discovered merely because it is evaluated.

The caller must explicitly call:

```python
mark_discovered(story)
```

The discovery history can be cleared in memory.

---

# 40. DISCOVERY FRESHNESS

Implemented freshness weighting.

Current half-life:

```text
24 hours
```

Approximate freshness factors:

```text
0 hours   → 1.0
24 hours  → 0.5
48 hours  → 0.25
72 hours  → 0.125
```

Freshness contributes:

```text
0 .. +20
```

Future timestamps are treated as age zero.

Stories without publication timestamps use neutral freshness behavior.

---

# 41. FEEDBACK SYSTEM

Implemented:

`intelligence/feedback.py`

Feedback types:

```text
LIKE
DISLIKE
MORE_LIKE_THIS
LESS_LIKE_THIS
TELL_ME_MORE
DO_NOT_TELL_ME_THIS
DISMISS
```

Per-event adjustments:

```text
LIKE                 +5
MORE_LIKE_THIS      +10
TELL_ME_MORE         +8
DISLIKE              -5
LESS_LIKE_THIS      -10
DO_NOT_TELL_ME_THIS -20
DISMISS              -8
```

Preferences are bounded:

```text
-50 .. +50
```

Feedback is tracked independently for:

* category
* entity
* source

Entity/category/source matching is case-insensitive.

---

# 42. FEEDBACK PERSISTENCE

Feedback is stored in SQLite.

`FeedbackProfile` starts clean in memory.

Persistent feedback is explicitly loaded with:

```python
load_persistent_feedback()
```

This design keeps normal unit tests isolated from persistent state.

---

# 43. FEEDBACK DECAY

Implemented time decay.

Current half-life:

```text
30 days
```

Approximate strength:

```text
0 days   → 1.0
30 days  → 0.5
60 days  → 0.25
90 days  → 0.125
```

Historical feedback is never deleted because of decay.

Only its current influence decreases.

New feedback receives full current strength.

---

# 44. FEEDBACK → INTELLIGENCE SCORING

Feedback is integrated into `IntelligenceScorer`.

Flow:

```text
base intelligence score
        ↓
feedback category adjustment
        ↓
feedback entity adjustment
        ↓
feedback source adjustment
        ↓
personalized score
```

The feedback contribution is bounded.

---

# 45. FEEDBACK HANDLER

Implemented:

`intelligence/feedback_handler.py`

It accepts an `IntelligenceStory` and extracts:

* story category
* entity names
* source

then records the appropriate `FeedbackType`.

---

# 46. FEEDBACK → DISCOVERY

Discovery now uses learned preferences.

Feedback contribution is bounded:

```text
-30 .. +30
```

Entity contribution is separately bounded:

```text
-20 .. +20
```

Positive learned preferences can increase discovery scores.

Negative learned preferences can suppress discovery.

Strong negative preferences can cause an otherwise moderate story to fall below the discovery threshold.

---

# 47. HUMOR SYSTEM

Implemented:

```text
intelligence/humor.py
intelligence/test_humor.py
```

Current humor system is:

* deterministic
* offline
* dependency-free
* template-based
* context-aware
* non-repeating within an engine instance

Supported styles include:

```text
light
playful
tech
observational
self_aware
```

The system detects topics such as:

* coding
* debugging
* compiling
* studying
* late night
* weather
* VYRA/self
* Python/C++/DSA

It does not call an LLM yet.

---

# 48. FUN-FACT SYSTEM

Implemented:

```text
intelligence/fun_facts.py
intelligence/test_fun_facts.py
```

Supported categories include:

```text
science
technology
history
space
nature
india
random
```

Features:

* confidence-based selection
* category filtering
* duplicate protection
* invalid-category protection

Currently local/in-memory.

Internet-backed fact retrieval is future work.

---

# 49. DISCOVERY POLICY

Implemented:

`intelligence/discovery_policy.py`

Current general discovery cooldown:

```text
180 minutes
```

Current fun-fact cooldown:

```text
360 minutes
```

Discovery policy is intentionally separate from the main InteractionEngine.

---

# 50. CURRENT INTELLIGENCE ARCHITECTURE

Current pipeline:

```text
Real intelligence source
        ↓
IntelligenceStory
        ↓
Deduplication
        ↓
Entity extraction
        ↓
Topic relevance
        ↓
Geographic relevance
        ↓
India relevance
        ↓
Technology/research relevance
        ↓
World relevance
        ↓
Intelligence scoring
        ↓
Feedback personalization
        ↓
Priority
        ↓
Delivery policy
        ↓
InteractionEngine
        ↓
SPEAK / WAIT
```

Discovery branch:

```text
IMPORTANT / INTERESTING
        ↓
IntelligenceQueue
        ↓
DiscoveryEngine
        ↓
feedback
+
freshness
+
repetition suppression
        ↓
DiscoveryCandidate
        ↓
DiscoveryPolicy
        ↓
InteractionEngine
```

---

# 51. USER PERSONALIZATION

VYRA now has the first real personalization loop:

```text
story
↓
user feedback
↓
feedback profile
↓
SQLite
↓
time-decayed preference
↓
future scoring
↓
future discovery
```

This is the foundation for longer-term adaptation.

---

# 52. DEVELOPMENT TOOL TEAM

The VYRA development workflow intentionally uses multiple AI tools.

Potential collaborators:

```text
ChatGPT
DeepSeek
Cursor
Claude / Claude Code
Codex
Blackbox AI
other coding/reasoning tools
```

Preferred workflow:

```text
architecture/task
→ one coding tool
→ tests
→ review
→ integration
→ Git checkpoint
```

Do not have multiple coding agents edit the same file simultaneously.

Use the tool best suited to the task rather than forcing every task through every platform.

---

# 53. TESTING RULE

When running Python package modules, prefer:

```text
python -m package.module
```

Examples:

```text
python -m intelligence.test_discovery
python -m intelligence.test_feedback
python -m intelligence.test_fun_facts
python -m intelligence.test_humor
python -m intelligence.test_queue
```

For syntax verification:

```text
python -m py_compile <files>
```

Do not change tests merely to hide an implementation bug.

---

# 54. GIT CHECKPOINT RULE

Git checkpoints should occur after a meaningful stable batch, not every tiny edit.

Preferred cycle:

```text
implement
↓
test
↓
integrate
↓
verify
↓
replace VYRA_STATE.md
↓
git checkpoint
```

Temporary debugging scripts should not be committed unless intentionally converted into reusable project tests.

---

# 55. CURRENT COMPLETION STATUS

Major completed areas include:

```text
Core VYRA
Ollama/Gemma
SQLite memory
Tasks/reminders
Scheduler
Activity monitoring
Context system
Interaction policy
Interaction engine
Proactive system
Daily session state
Morning briefing foundation
Weather
Memory retrieval
Calendar abstraction
Windows location
Reverse geocoding
LocationService
Current location context
Important places
Place relationships
IntelligenceStory
Entity extraction
Entity-aware scoring
RSS/Atom source adapter
Source configuration
Source registry
Source factory
Source ingestion
Deduplication
Topic relevance
Geographic relevance
India relevance
Technology/research relevance
World relevance
Priority engine
Delivery policy
Intelligence → InteractionEngine
Current affairs mode
Intelligence queue
Discovery engine
Discovery feedback personalization
Discovery repetition suppression
Discovery freshness
Fun-fact system
Humor system
Persistent feedback
Feedback decay
Feedback-aware intelligence scoring
Feedback-aware discovery
```

---

# 56. CURRENT STEP

**7.76 — Discovery / feedback integration refinement**

The next goal is to improve how VYRA combines learned preferences, freshness, discovery timing, and the InteractionEngine before moving deeper into autonomous/proactive personalization.

---

# 57. IMMEDIATE NEXT STEPS

```text
7.76  Discovery / feedback integration refinement

7.77  Discovery timing with InteractionEngine

7.78  Persistent discovery history

7.79  Personalized discovery frequency

7.80  User-controlled information preferences

7.81  Better story/entity preference explanations

7.82  Feedback-aware current-affairs selection

7.83  Feedback-aware morning intelligence

7.84  Surprise/fun-fact selection

7.85  Natural humor integration

7.86  Reddit/community intelligence

7.87  Research/deep-tech discovery

7.88  Company/India-market intelligence

7.89  Persistent intelligence history

7.90  Longitudinal intelligence trends

8.0   Semantic memory retrieval

8.1   Embeddings

8.2   Memory deduplication

8.3   Memory importance

8.4   Memory decay / supersession

8.5   Context-aware memory selection

9.0   Model router

9.1   Local model provider

9.2   NVIDIA/NIM provider

9.3   DeepSeek provider

9.4   Additional cloud providers

9.5   Specialist model routing

9.6   Automatic fallback

10.0  Voice

11.0  Vision

12.0  Computer interaction

13.0  Personalization

14.0  Personality / presence

15.0  Advanced intelligence

16.0  PyTorch/custom ML

17.0  Dockerized services

18.0  Controlled self-improvement

19.0  Long-term VYRA evolution
```

---

# 58. LONG-TERM MODEL / TOOL ROADMAP

Future model providers may include:

```text
Ollama/local models
NVIDIA NIM
DeepSeek
cloud providers
specialist models
vision models
speech models
embedding models
```

Future tool orchestration may allow VYRA herself to call appropriate providers/tools based on:

* privacy
* task complexity
* latency
* cost
* reliability
* capability

VYRA should not become dependent on any single external provider.

---

# 59. LONG-TERM ML ROADMAP

PyTorch should be introduced when VYRA has a concrete learned-model requirement.

Possible applications:

* activity classification
* personalized ranking
* recommendation
* learned relevance
* semantic intelligence
* vision

TensorFlow is optional and should only be introduced for a concrete technical reason.

---

# 60. LONG-TERM DOCKER ROADMAP

Docker may eventually isolate:

* model services
* embedding service
* research service
* vector database
* voice service
* vision service
* agent sandbox
* self-improvement sandbox

Docker should be introduced when these become actual service boundaries.

---

# 61. LONG-TERM SELF-IMPROVEMENT

Desired architecture:

```text
observe
↓
identify improvement
↓
propose change
↓
generate candidate
↓
sandbox
↓
test
↓
benchmark
↓
review
↓
version
↓
deploy
↓
observe
```

VYRA should not silently rewrite production code without controlled evaluation and rollback.

---

# 62. LONG-TERM VYRA

VYRA should eventually be able to:

```text
remember
reason
research
observe context
understand location
understand important places
learn preferences
discover useful information
choose when to speak
choose when to wait
use multiple AI models
use tools/APIs
provide humor
provide useful surprises
adapt over time
maintain continuity
```

The goal is not maximum information output.

The goal is:

**good judgment + continuity + personality + usefulness.**

---

# 63. LAST UPDATED

Completed through:

**7.75 — Discovery Freshness**

Next:

**7.76 — Discovery / feedback integration refinement**
