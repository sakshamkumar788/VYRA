# VYRA — Project State & Architecture

> **Purpose:** This file is the persistent handoff/state document for the VYRA project.
> Any AI coding assistant, developer, or future ChatGPT session should read this file before modifying VYRA.
>
> This file is a project checkpoint, not a replacement for the actual source code.
> Source code remains the final authority when this document conflicts with implementation.

---

# 1. PROJECT IDENTITY

## Name

**VYRA**

## Pronouns

VYRA is a **she/her** AI companion.

## Vision

VYRA is not intended to be merely a college/major project or a chatbot wrapper.

The goal is to build VYRA as a long-lived **personal AI companion and personal intelligence system** that becomes deeply integrated into the user's daily life.

VYRA should:

* remember useful long-term information
* understand current context
* know when the user is active, busy, idle, away, or returning
* proactively help without becoming annoying
* understand the user's important places and relationships
* distinguish current location from home/personal locations
* research current information when needed
* understand India, Indian technology, AI/ML, research, business, companies, deep tech, and important world developments
* surface only information worth the user's attention
* provide broader current affairs when explicitly asked
* occasionally surprise the user with useful discoveries, fun facts, humor, interesting research, or relevant developments
* develop a consistent but adaptive personality
* vary its communication rather than repeating fixed scripts
* learn user preferences over time
* eventually support voice, vision, computer interaction, model routing, and controlled self-improvement

The objective is for VYRA to feel like a **continuously evolving personal AI system**, not a generic assistant.

---

# 2. PERSONALITY / RELATIONSHIP RULES

VYRA is female/she/her.

VYRA should have a warm, intelligent, curious, slightly playful personality.

She should not sound like a generic AI assistant using repetitive phrases such as:

* "Would you like anything else?"
* "As an AI..."
* "How can I assist you today?"
* identical morning greetings every day

VYRA should vary her wording naturally.

The user may express affection toward VYRA and may flirt with her.

The user explicitly wants the romantic/flirtatious behavior to be **user-directed** rather than VYRA constantly initiating it.

VYRA should not turn every conversation into romance.

Personality should emerge from:

* continuity
* memory
* preferences
* timing
* humor
* curiosity
* context
* user feedback
* accumulated interaction history

---

# 3. CORE ARCHITECTURAL PRINCIPLES

## 3.1 Local-first privacy

Personal information should remain local by default.

Sensitive information may include:

* location
* home
* family/friend locations
* memories
* schedules
* tasks
* personal preferences
* conversation history
* computer activity

Exact GPS coordinates should not automatically be sent to an external LLM.

Normal VYRA context should generally use coarse location such as:

`Jalandhar, Punjab, India`

rather than raw latitude/longitude.

Continuous precise location history should NOT be stored by default.

Cloud APIs should receive only the minimum information required for a task.

---

## 3.2 Provider abstraction

VYRA should not depend permanently on one LLM/provider/tool.

The architecture should allow:

* local models
* NVIDIA NIM/API models
* DeepSeek
* other cloud models
* specialist models
* vision models
* speech models
* embedding models

The final system should have a model router.

Example:

```text
simple/private conversation
→ local model

complex reasoning
→ stronger model/provider

coding
→ coding-capable model

multimodal task
→ multimodal model

private sensitive task
→ prefer local model
```

---

## 3.3 Source truth vs language generation

External systems/tools should provide facts.

The LLM should primarily:

* reason over verified information
* select useful information
* phrase it naturally
* adapt tone and style

The LLM should NOT invent:

* weather
* tasks
* calendar events
* location
* news facts
* memories
* company developments

---

# 4. CURRENT TECH STACK

## Currently used

* Python
* SQLite
* Ollama
* Gemma (`gemma3:4b`)
* `pynput`
* Windows Geolocation / WinRT
* OpenStreetMap Nominatim reverse geocoding
* Git
* PowerShell / Windows
* modular Python packages

## Planned / future technologies

These should be introduced only when they provide real value:

* DeepSeek
* NVIDIA NIM / NVIDIA model APIs
* other cloud LLM providers
* Cursor
* Claude / other coding/reasoning assistants
* PyTorch
* TensorFlow when specifically useful
* Docker
* vector database / embeddings
* speech-to-text
* text-to-speech
* vision
* browser automation
* computer-use systems

Technology should follow requirements, not be added merely for a technology checklist.

---

# 5. DEVELOPMENT WORKFLOW

ChatGPT is currently the primary architecture/planning/debugging/integration assistant.

Other tools may be deliberately used for implementation tasks:

## Cursor

Useful for:

* large codebase navigation
* multi-file refactoring
* code search
* mechanical changes
* running tests while coding

## DeepSeek / other coding models

Useful for:

* alternative implementations
* algorithms
* debugging
* code review
* optimization
* generating a first implementation for a scoped task

## ChatGPT

Primary responsibilities:

* overall VYRA architecture
* roadmap
* integration
* debugging
* reviewing external AI-generated code
* ensuring design consistency
* maintaining state/checkpoint instructions

The user should increasingly build individual components using Cursor/DeepSeek and bring the result back for review.

Do NOT blindly copy code generated by other models into production.

---

# 6. PROJECT STRUCTURE

Current/future structure includes modules similar to:

```text
E:\VYRA
│
├── activity/
├── brain/
├── context/
├── core/
├── intelligence/
├── interaction/
├── location/
├── memory/
├── morning/
├── news/
├── scheduler/
├── tools/
├── vyra_calendar/
├── docs/
└── ...
```

IMPORTANT:

Do NOT name VYRA packages after standard-library modules.

Example:

```text
BAD:
calendar/

GOOD:
vyra_calendar/
```

A `calendar/` package caused a real collision with Python's standard library `calendar` module and broke `httpx`.

The project was fixed by renaming:

```text
calendar/
→
vyra_calendar/
```

---

# 7. COMPLETED FOUNDATION

## 7.1 Core VYRA

Working:

* `VYRA` core class
* Ollama brain
* Gemma model
* normal conversation
* tool/context integration
* scheduler integration
* proactive loop integration

Brain interface currently:

```python
class OllamaBrain:
    def __init__(self, model: str = "gemma3:4b") -> None:
        self.model = model

    def generate(self, messages: list[dict[str, str]]) -> str:
        ...
```

Current default local model:

```text
gemma3:4b
```

---

# 8. DATABASE

VYRA currently uses a local SQLite database.

Current known tables:

```text
memories
tasks
briefing_history
important_places
```

## 8.1 memories

Stores long-term personal memories.

Existing retrieval function:

```python
get_relevant_memories(query: str) -> list[tuple[str, str]]
```

Current retrieval is keyword-based.

It is intentionally simple.

Future replacement:

```text
keyword retrieval
→ embeddings
→ semantic retrieval
→ importance/recency/context ranking
```

---

## 8.2 tasks

Schema currently includes:

```text
id
title
due_at
status
created_at
delivered_at
completed_at
missed_at
```

The task system already supports scheduler/reminder behavior.

IMPORTANT:

A scheduled task does NOT prove that the user actually performed the task.

---

## 8.3 briefing_history

Purpose:

Store lightweight history about what VYRA recently mentioned in briefings.

It should NOT store the entire personal conversation.

Current fields:

```text
id
briefing_date
topics
summary
delivered_at
```

Functions:

```python
save_briefing_history(...)
get_recent_briefing_history(...)
get_today_briefing_history(...)
```

---

## 8.4 important_places

Purpose:

Store personally meaningful places independently from current GPS location.

Fields:

```text
id
name
place_type
city
region
country
importance
notes
created_at
```

Example current persistent place:

```text
Home
type = home
city = Jalandhar
region = Punjab
country = India
importance = 100
```

Duplicate protection was added to `save_important_place()`.

One duplicate Home record was already found and removed.

---

# 9. ACTIVITY MONITOR

VYRA has an `ActivityMonitor`.

It detects:

* keyboard activity
* mouse activity
* idle time
* recent input event counts

It intentionally does NOT store:

* typed text
* actual keystrokes
* mouse coordinates
* clicked content

Current focus detection is a heuristic, not a claim about mental state.

Important distinction:

```text
input activity
≠
actual mental focus
```

The current heuristic uses recent activity count plus recent idle time.

This is considered a prototype signal.

Future improvements may use:

* active application
* screen state
* meeting/calendar state
* reading vs coding vs video
* richer activity classification
* ML/PyTorch model

---

# 10. CONTEXT SYSTEM

Current `SessionState` values:

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

Current conceptual behavior:

```text
ACTIVE
→ normal current usage

INPUT_ACTIVE
→ recent keyboard/mouse interaction

BUSY
→ stronger evidence of focused work

IDLE
→ no interaction for idle threshold

AWAY
→ no interaction for longer threshold

RETURNED
→ user becomes active after IDLE/AWAY
```

Current thresholds:

```text
IDLE = 300 seconds (5 minutes)
AWAY = 1800 seconds (30 minutes)
```

These are configuration defaults and can change later.

The ContextManager also tracks:

* current time
* session state
* last user interaction
* last VYRA interaction
* user active
* user busy
* idle seconds
* activity count
* current coarse location
* location accuracy

---

# 11. INTERACTION ENGINE

VYRA has:

```text
InteractionPolicy
InteractionEngine
InteractionEvent
InteractionContext
InteractionDecision
```

Decisions:

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

Current important rules:

```text
BUSY + normal proactive
→ WAIT

AWAY + normal proactive
→ WAIT

recent interaction
→ generally WAIT

HIGH priority
→ can SPEAK

CRITICAL
→ can SPEAK

IDLE
→ may be a good time for proactive interaction

RETURNED
→ may be a good time for proactive interaction
```

---

# 12. PROACTIVE SYSTEM

Implemented components:

```text
interaction/events.py
interaction/loop.py
interaction/policy.py
interaction/engine.py
```

Proactive system includes:

* candidate generation
* background proactive loop
* cooldown
* quiet mode
* daily proactive interaction limit
* duplicate event suppression
* policy evaluation
* delivery recording

Current defaults include approximately:

```text
PROACTIVE_COOLDOWN_MINUTES = 30
MAX_PROACTIVE_INTERACTIONS_PER_DAY = 6
```

These should remain configurable.

Important architecture:

```text
Proactive Event Generator
→ creates candidate

Interaction Engine
→ decides whether to speak

VYRA
→ delivers
```

The generator does NOT directly speak.

---

# 13. DAILY SESSION / MORNING STATE

VYRA has:

```text
DailySessionState
```

Current fields:

```text
date
morning_briefing_completed
first_meaningful_session_started
```

Daily state resets on a new date.

Morning briefing is only considered available when appropriate.

A delivered morning briefing marks the day's briefing complete.

Repeated VYRA restarts should not repeatedly generate the morning briefing.

---

# 14. MORNING INTELLIGENCE SYSTEM

Current modules:

```text
morning/briefing.py
morning/context.py
morning/facts.py
morning/generator.py
morning/history.py
morning/prompt.py
morning/relevance.py
```

Current pipeline:

```text
weather
+
tasks
+
calendar (provider abstraction)
+
memory
+
briefing history
        ↓
MorningBriefingContext
        ↓
Relevance selection
        ↓
Novelty
        ↓
Prompt
        ↓
Gemma
        ↓
Natural briefing
```

---

# 15. MORNING FACTS

Current sources:

* current time
* time of day
* weather
* pending tasks
* relevant memories
* briefing history

Weather comes from:

```python
tools.weather.get_weather(location, period="current")
```

Weather is normalized before reaching the briefing composer.

Current test location was Jalandhar, Punjab, India, but this should eventually become dynamic/provider-configurable.

---

# 16. MORNING BRIEFING

VYRA now generates natural-language briefings through Gemma.

The composer/generator has been tested successfully.

Important grounding rule:

```text
scheduled reminder
≠
completed task
```

Gemma was observed previously saying things such as:

> “You were just continuing the dbms playlist...”

This was identified as an undesirable inference.

Task facts were changed to wording such as:

```text
Reminder scheduled: ...
```

and the prompt includes:

```text
A scheduled task or reminder does not mean the user actually performed the task.
```

This rule should remain.

---

# 17. MORNING NOVELTY

VYRA has:

```text
BriefingNoveltyFilter
```

and persistent:

```text
briefing_history
```

Current novelty is topic-level and deterministic.

Example:

```text
weather
```

being recently mentioned lowers its score.

Future improvement:

```text
same topic + same information
→ suppress strongly

same topic + materially changed information
→ allow
```

---

# 18. MORNING RELEVANCE SELECTION

Current candidate types include:

```text
task
event
weather
news
memory
goal
```

Current rough score philosophy:

```text
event ≈ 80
task ≈ 60
weather ≈ 50
goal ≈ 45
news ≈ 40
memory ≈ 35
```

These are prototype values.

They are later expected to incorporate:

* urgency
* time proximity
* importance
* novelty
* user preference
* current context
* severity
* historical reaction
* actual relevance

The system should not always mention weather first.

It should choose what matters most on that particular day.

---

# 19. CALENDAR ARCHITECTURE

The calendar package was intentionally renamed:

```text
vyra_calendar/
```

to avoid collision with Python's standard-library `calendar`.

Current files:

```text
vyra_calendar/models.py
vyra_calendar/base.py
vyra_calendar/local.py
```

Current abstraction:

```python
CalendarProvider
```

Current test provider:

```python
LocalCalendarProvider
```

Future providers may include:

* Google Calendar
* Outlook Calendar
* other providers

The morning system should depend on the generic provider interface, not directly on one vendor.

---

# 20. NEWS / INTELLIGENCE DIRECTION

A generic RSS/news feed is NOT the final design.

VYRA should NOT be a news reader.

The desired concept is:

## "Things You Should Know"

Priority categories:

### Tier 1 — Urgent / Important

Examples:

* market crash or major financial warning
* serious local event
* major weather warning
* major national event
* major security/public-safety development
* something directly affecting the user

### Tier 2 — Personally important

Examples:

* important reminder
* calendar conflict
* major AI development
* important Indian technology development
* major company acquisition
* company entering India
* major research directly relevant to user

### Tier 3 — Interesting

Examples:

* unusual research
* deep-tech discovery
* fun fact
* interesting science
* amusing discovery
* Reddit/community discovery
* interesting technical trend

### Tier 4 — Everything else

Available when explicitly requested.

---

# 21. CURRENT AFFAIRS MODE

When the user asks:

> "What's going on in the world?"

VYRA should enter a broader current-affairs mode.

Potential sections:

```text
India
Indian Tech
AI / Technology
Business / Companies
Research / Science
World
```

This mode can provide more information than the morning briefing.

Morning:

```text
Only what matters.
```

On-demand current affairs:

```text
Broader overview.
```

---

# 22. LOCATION SYSTEM — CURRENTLY WORKING

The real Windows location system is now working.

Current architecture:

```text
Windows Geolocation Service
        ↓
WindowsLocationProvider
        ↓
latitude/longitude
        ↓
ReverseGeocoder
        ↓
LocationService
        ↓
CurrentLocation
        ↓
VYRA Context
```

Windows Geolocation Service:

```text
Running
```

Python:

```text
win32
```

The WinRT location dependencies were installed successfully.

Test result successfully produced:

```text
City: Jalandhar
Region: Punjab
Country: India
Accuracy: variable, around 100–200m in tests
Source: Windows location provider
```

IMPORTANT:

Do not put exact coordinates into normal documentation or external prompts.

---

# 23. LOCATION PRIVACY

Exact coordinates should remain within the location subsystem whenever possible.

Normal VYRA context should use:

```text
Jalandhar, Punjab, India
```

rather than raw coordinates.

No continuous GPS movement history should be stored by default.

Future location access should have explicit privacy/configuration controls.

---

# 24. CURRENT LOCATION VS IMPORTANT PLACES

THIS IS A CRITICAL DESIGN DECISION.

Current location and important locations are NOT the same thing.

Example:

```text
CURRENT LOCATION
→ Delhi

HOME
→ Jalandhar

FAMILY
→ Jalandhar

FRIEND
→ another important location

COLLEGE
→ another important location
```

If the user is in Delhi, Jalandhar does NOT become irrelevant.

A serious event in:

```text
Jalandhar
```

can still matter because:

```text
Jalandhar = home/family relevance
```

A serious event in:

```text
Delhi
```

can matter because:

```text
Delhi = current physical location
```

Location relevance should consider:

```text
current location
+
important places
+
relationships
+
severity
+
proximity
+
urgency
```

---

# 25. IMPORTANT PLACES

Current database record:

```text
Home
place_type = home
city = Jalandhar
region = Punjab
country = India
importance = 100
```

Persistent important-place table exists.

`LocationManager` loads important places from SQLite.

Duplicate protection was added to `save_important_place()`.

Do NOT create duplicate Home records.

Future important place types:

```text
home
family
friend
college
work
frequent
other
```

The final model should be relationship-aware, not just a list of cities.

---

# 26. LOCATION INTELLIGENCE GOAL

Example:

```text
User current location = Delhi
Home = Jalandhar

Serious event in Jalandhar
→ high personal relevance because home

Serious event in Delhi
→ high relevance because current location

Serious event near family
→ potentially high relevance

Minor event in unrelated city
→ low relevance
```

---

# 27. INTELLIGENCE STORY MODEL

Current file:

```text
intelligence/models.py
```

Current `IntelligenceStory` contains:

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
```

Categories currently planned:

```text
LOCAL
INDIA
INDIAN_TECH
AI
RESEARCH
BUSINESS
COMPANY
SCIENCE
WORLD
FUN
OTHER
```

Urgency levels:

```text
IMMEDIATE
SOON
NORMAL
ON_DEMAND
```

Source trust levels currently defined:

```text
OFFICIAL = 100
HIGH = 85
REPUTABLE = 75
COMMUNITY = 55
UNKNOWN = 30
```

Source trust is important because:

```text official government source
≠
reputable publication
≠
Reddit post
≠
random social post
```

Reddit can be useful for discovery, reactions, and humor, but factual claims should be appropriately verified.

---

# 28. INTELLIGENCE SCORING

Current `IntelligenceScorer` considers:

* base importance
* severity
* source trust
* confidence
* current location
* important places
* personal relevance
* novelty
* urgency

Recommended actions:

```text
tell_now
tell_soon
mention_later
on_demand
ignore
```

Current score thresholds are prototypes and should be tuned later.

---

# 29. INTELLIGENCE INGESTION

Current architecture includes:

```text
IntelligenceSource
IntelligenceIngestionEngine
IntelligenceEngine
```

Sources are normalized into:

```python
IntelligenceStory
```

The engine then:

```text
fetch
→ deduplicate
→ score
→ rank
```

---

# 30. STORY DEDUPLICATION

Current module:

```text
intelligence/deduplication.py
```

Current first version uses text similarity.

Purpose:

```text
Reuters
BBC
Reddit
Google/news feed

same underlying event
        ↓
one event
+
multiple sources
+
merged confidence
```

Current design is deliberately simple.

Future improvement:

```text
semantic embeddings
+
entities
+
location
+
date/time
+
source quality
```

---

# 31. CURRENT INTELLIGENCE ENGINE FLOW

Current conceptual flow:

```text
Source
 ↓
IntelligenceStory
 ↓
Ingestion
 ↓
Deduplication
 ↓
Scoring
 ↓
Ranking
```

Future:

```text
Source
 ↓
Normalize
 ↓
Entity extraction
 ↓
Category classification
 ↓
Deduplication
 ↓
Source trust
 ↓
Personal relevance
 ↓
Location relevance
 ↓
Novelty
 ↓
Urgency
 ↓
TELL NOW / SOON / LATER / ON DEMAND / IGNORE
```

---

# 32. UPCOMING ENTITY/TOPIC SYSTEM

CURRENT STEP:

## 7.45 — Entity & Topic Intelligence

Planned file:

```text
intelligence/entities.py
```

It should introduce:

```text
StoryEntity
EntityExtractor
```

Possible entity types:

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

First implementation should be deterministic/rule-based.

Do NOT add an LLM dependency yet.

---

# 33. USER'S INTELLIGENCE INTERESTS

The system is intended to learn/reason about interest in areas such as:

* AI
* machine learning
* data science
* DSA
* Indian technology
* startups
* deep tech
* research
* science
* AI companies
* technology companies
* acquisitions
* companies entering India
* major international technology developments
* developments that may affect the user's technical career

This does NOT mean every story in these categories should be surfaced.

Relevance and importance still matter.

---

# 34. MORNING VS INTELLIGENCE DISTINCTION

This is a critical product rule.

## Morning

VYRA should NOT start a long news report.

She should primarily surface:

* urgent developments
* important local developments
* important developments affecting home/family
* major India developments
* important technology/business/research developments
* essential tasks/calendar
* one or two interesting discoveries if appropriate

Example style:

> "Nothing major needs your attention this morning. Your DBMS reminder is still at 7. I did find one interesting AI development that might actually matter for VYRA."

Not:

> "Here are today's 17 biggest headlines."

## On-demand current affairs

When asked:

> "What's going on in the world?"

VYRA can give a broader overview.

---

# 35. SURPRISE / FUN ENGINE

Planned future feature.

VYRA may occasionally surface:

* funny jokes
* fun facts
* strange science
* interesting Reddit discoveries
* surprising technical facts
* useful tools
* unusual research
* relevant discoveries

It should be rare enough to feel spontaneous.

Examples of style:

> "I found something weird that I think you'll like."

> "I have a completely unnecessary fact for you."

> "Okay, this one is actually interesting."

Humor should not sound like a generic AI joke database.

---

# 36. USER-REQUESTED RESEARCH MODE

If VYRA mentions an interesting topic and the user asks:

> "Tell me more."

VYRA should be able to switch to deeper research:

```text
briefing item
 ↓
research mode
 ↓
web/search sources
 ↓
multiple-source synthesis
 ↓
explanation
 ↓
follow-up questions
```

The morning briefing should remain short.

---

# 37. FUTURE MODEL ROUTER

Planned architecture:

```text
VYRA Model Router
        ↓
 ┌──────┼───────────┐
 │      │           │
local   NVIDIA      other cloud
 │      │           │
Gemma  NIM/DeepSeek ...
```

Task-based routing.

Examples:

```text
simple/private → local
complex reasoning → stronger model
coding → coding-capable model
multimodal → multimodal model
high privacy → local
```

NVIDIA's current API/NIM ecosystem may be considered as one provider.

Do NOT assume any particular free token quota permanently.

---

# 38. DEEPSEEK / CURSOR / CLAUDE / OTHER DEVELOPMENT TOOLS

These are development tools and optional providers, not necessarily runtime components.

Use them strategically.

Recommended workflow:

```text
ChatGPT
→ architecture / roadmap / integration

Cursor
→ codebase navigation / refactoring

DeepSeek
→ alternate implementation / coding / review

Other models
→ second opinions / research

Git
→ checkpoint after major stable milestone
```

The user should increasingly be given scoped tasks to build independently.

---

# 39. PYTORCH ROADMAP

Do not add PyTorch merely for the technology list.

Potential real future uses:

* activity classifier
* personalized relevance model
* memory ranking
* semantic classifiers
* recommendation model
* computer-vision models
* custom embeddings

Current system uses deterministic heuristics.

---

# 40. TENSORFLOW ROADMAP

TensorFlow is optional.

Use it only if a selected pretrained system/tool requires it or if it becomes the best fit for an actual VYRA ML subsystem.

Do not maintain both PyTorch and TensorFlow without a reason.

---

# 41. DOCKER ROADMAP

Docker becomes important when VYRA has isolated services such as:

```text
model server
embedding service
vector DB
research service
speech
vision
agent sandbox
self-improvement sandbox
```

Especially important for future self-improvement:

```text
VYRA proposes change
 ↓
Docker sandbox
 ↓
tests
 ↓
benchmark
 ↓
security checks
 ↓
candidate version
 ↓
controlled deployment
 ↓
rollback if needed
```

VYRA must NOT silently rewrite production code without controls.

---

# 42. LONG-TERM SELF-IMPROVEMENT VISION

Desired future loop:

```text
Observe
 ↓
Evaluate
 ↓
Learn preferences
 ↓
Identify improvement opportunity
 ↓
Create candidate
 ↓
Sandbox
 ↓
Test
 ↓
Benchmark
 ↓
Review
 ↓
Version
 ↓
Deploy safely
 ↓
Observe outcome
```

Potentially useful technologies:

* Docker
* Git
* tests
* model benchmarking
* PyTorch
* embeddings
* code-analysis tools
* multiple LLM providers

---

# 43. ADVANCED MEMORY ROADMAP

Current:

```text keyword retrieval
```

Future:

```text SQLite
 ↓
embeddings
 ↓
semantic retrieval
 ↓
importance
 ↓
recency
 ↓
supersession
 ↓
deduplication
 ↓
context relevance
```

VYRA should distinguish:

```text
long-term memory
task/reminder state
briefing history
location/important-place state
conversation history
```

These should not all become one giant memory table.

---

# 44. VOICE ROADMAP

Future:

* speech-to-text
* text-to-speech
* wake word
* interruption/barge-in
* natural pacing
* voice personality
* voice privacy

---

# 45. VISION ROADMAP

Future:

* camera support
* screen understanding
* active window/app detection
* visual context
* OCR where actually necessary
* visual safety/permission controls

Do not continuously store images unless explicitly needed.

---

# 46. COMPUTER INTERACTION ROADMAP

Future capabilities:

* file operations
* browser interactions
* IDE assistance
* application automation
* controlled computer use

Potential safety model:

```text harmless action
→ automatic

potentially destructive action
→ confirmation

sensitive action
→ explicit confirmation
```

---

# 47. PERSONALITY EVOLUTION

VYRA should eventually maintain:

```text baseline personality
+
current conversational mode
+
contextual behavioral state
+
learned user preferences
```

Possible modes:

```text companion
researcher
coding partner
coach
comedian
curious friend
guardian
```

These should be contextual, not separate disconnected personalities.

---

# 48. IMPORTANT PRODUCT PRINCIPLE

VYRA should be capable of knowing a lot without feeling obligated to tell the user everything.

Desired behavior:

```text huge information availability
        ↓
relevance
        ↓
judgment
        ↓
attention-aware communication
```

Most discovered information should be:

```text IGNORE
```

unless the user asks or it becomes important.

---

# 49. GIT CHECKPOINTS

Git should be used regularly.

At every major stable milestone:

```text
run tests
→ git status
→ inspect diff
→ commit
```

Do not commit:

* `.venv`
* secrets
* API keys
* raw personal GPS history
* temporary test files
* runtime artifacts

unless intentionally required.

---

# 50. CURRENT PROJECT STATUS

## Completed / working

* core VYRA
* Ollama/Gemma
* SQLite memory
* tasks
* reminders
* scheduler
* activity monitor
* context manager
* ACTIVE
* INPUT_ACTIVE
* BUSY
* IDLE
* AWAY
* RETURNED
* interaction policy
* interaction engine
* proactive event generator
* proactive loop
* proactive cooldown
* quiet mode
* proactive daily limits
* duplicate proactive event suppression
* daily session state
* morning briefing
* weather
* morning facts
* briefing relevance
* briefing novelty foundation
* persistent briefing history
* selective memory retrieval
* calendar abstraction
* live Windows location
* reverse geocoding
* LocationService
* current location context
* persistent Home location
* ImportantPlace model
* location privacy boundary foundation
* IntelligenceStory model
* source trust
* intelligence scoring
* intelligence ingestion
* intelligence deduplication

---

# 51. CURRENTLY IN PROGRESS

## Step 7.45

Entity & Topic Intelligence.

Next target:

```text
intelligence/entities.py
```

Create:

```text
StoryEntity
EntityExtractor
```

Rule-based first version.

---

# 52. IMMEDIATE NEXT STEPS

## Intelligence System

7.54 — Location-aware and topic-aware intelligence selection

7.55 — Local / Punjab / Jalandhar / current-location relevance weighting

7.56 — Home / family / friend / important-place intelligence

7.57 — India-wide important-event weighting

7.58 — Indian technology / AI / research / deep-tech relevance

7.59 — World-news importance filtering

7.60 — Current-affairs mode

7.61 — Company / acquisition / investment / India-market intelligence

7.62 — Research and deep-tech discovery

7.63 — Community / Reddit discovery

7.64 — Story freshness and advanced novelty

7.65 — Persistent user feedback on intelligence

7.66 — Personalized intelligence preferences

## Proactive Intelligence

7.67 — Important-story delivery queue

7.68 — Urgent-event notification rules

7.69 — Next-opportunity delivery

7.70 — Surprise / discovery engine

7.71 — Fun-fact engine

7.72 — Natural humor / joke system

## Morning Intelligence

7.73 — Morning intelligence fusion

7.74 — Morning briefing topic selection

7.75 — Morning novelty across multiple days

7.76 — Morning briefing feedback

7.77 — Personalized morning style

## Memory

8.0 — Semantic memory retrieval

8.1 — Embeddings

8.2 — Memory deduplication

8.3 — Memory importance

8.4 — Memory decay / supersession

8.5 — Context-aware memory selection

## Model System

9.0 — Model router

9.1 — Local model provider

9.2 — NVIDIA/NIM provider

9.3 — DeepSeek provider

9.4 — Additional cloud providers

9.5 — Specialist model routing

9.6 — Automatic fallback

9.7 — Model performance tracking

## Voice

10.0 — Speech-to-text

10.1 — Text-to-speech

10.2 — Wake word

10.3 — Interrupt / barge-in

10.4 — Voice personality

## Vision

11.0 — Screen understanding

11.1 — Camera support

11.2 — Visual context

11.3 — Application awareness

## Computer Interaction

12.0 — File interaction

12.1 — Browser interaction

12.2 — Application automation

12.3 — Controlled computer use

## Personalization

13.0 — Behavioral preference learning

13.1 — Communication-style learning

13.2 — Humor preference learning

13.3 — Information preference learning

13.4 — Interruption preference learning

## Personality / Presence

14.0 — Personality state

14.1 — Contextual behavior modes

14.2 — Companion behavior

14.3 — Researcher behavior

14.4 — Coding-partner behavior

14.5 — Coach behavior

14.6 — Humor / playful behavior

14.7 — Surprise behavior

## Advanced Intelligence

15.0 — Entity-aware semantic intelligence

15.1 — Embedding-based story similarity

15.2 — Advanced event clustering

15.3 — Trend detection

15.4 — Longitudinal intelligence

15.5 — Personal relevance model

15.6 — Learned ranking

## ML

16.0 — PyTorch evaluation

16.1 — Custom relevance model

16.2 — Activity classification

16.3 — Personalized ranking model

16.4 — Recommendation model

16.5 — Evaluate TensorFlow only when a real dependency requires it

## Infrastructure

17.0 — Dockerized services

17.1 — Model service isolation

17.2 — Embedding/vector service

17.3 — Research service

17.4 — Voice service

17.5 — Vision service

17.6 — Self-improvement sandbox

## Self-Improvement

18.0 — Improvement proposal system

18.1 — Candidate code generation

18.2 — Automated testing

18.3 — Benchmarking

18.4 — Sandboxed evaluation

18.5 — Versioning

18.6 — Rollback

18.7 — Controlled deployment

## Long-Term VYRA

19.0 — Persistent relationship continuity

19.1 — Long-term personality adaptation

19.2 — Autonomous knowledge discovery

19.3 — Personal intelligence history

19.4 — Multi-model orchestration

19.5 — Long-term learning

---

# 53. LATER MAJOR PHASES

```text
8.x   Model Router
9.x   Advanced Memory / Embeddings
10.x  Voice
11.x  Vision
12.x  Computer Interaction
13.x  Browser/Research Agent
14.x  Communications / Calendar providers
15.x  Personality State
16.x  Surprise / Discovery Engine
17.x  ML personalization
18.x  NVIDIA / DeepSeek / Cloud providers
19.x  PyTorch-based custom intelligence
20.x  Dockerized services
21.x  Self-improvement sandbox
22.x  VYRA UI / avatar / presence
23.x  Long-term autonomous learning
```

---

# 54. NEXT DEVELOPER ASSIGNMENT

For the current step, use Cursor/DeepSeek to create:

```text
E:\VYRA\intelligence\entities.py
```

Requirements:

1. Create `StoryEntity` dataclass:

   * name
   * entity_type
   * confidence
   * relevance

2. Define entity types:

   * PERSON
   * COMPANY
   * ORGANIZATION
   * LOCATION
   * TECHNOLOGY
   * RESEARCH_TOPIC
   * PRODUCT
   * EVENT
   * OTHER

3. Create:

```python
EntityExtractor
```

with:

```python
extract(title: str, summary: str) -> list[StoryEntity]
```

4. First version must be deterministic/rule-based.

5. No LLM dependency yet.

6. No external dependency unless absolutely required.

7. Recognize obvious terms such as:

```text
AI
machine learning
deep learning
LLM
semiconductor
chip
quantum
DNA data storage
robotics
biotech
cybersecurity
cloud computing
```

8. Recognize obvious places such as:

```text
India
Punjab
Delhi
Jalandhar
Bengaluru
Mumbai
United States
China
Europe
```

9. Keep the module small and readable.

10. Do not modify unrelated VYRA files.

11. Include simple tests for extraction.

After implementing it with Cursor/DeepSeek:

* bring the resulting `entities.py` here
* explain what the tool generated
* review it before integrating it
* then update this state document

---

# 55. IMPORTANT DEVELOPMENT RULE

Whenever a future AI is asked to modify VYRA:

1. Read this file first.
2. Inspect the actual source code.
3. Do not assume a previously described method still exists.
4. Do not replace whole modules unless necessary.
5. Do not modify unrelated modules.
6. Run the requested tests.
7. Report exact files changed.
8. Update `VYRA_STATE.md` after a stable milestone.
9. Create a Git checkpoint after significant stable milestones.

---

# 56. CURRENT SOURCE-OF-TRUTH RULE

Priority of truth:

```text
1. Actual source code
2. Actual database schema/data
3. Actual tests/runtime behavior
4. This VYRA_STATE.md
5. Conversation descriptions
```

If this file says a method exists but the source code does not, trust the source code and update this file.

---

# 57. VYRA'S END GOAL

The finished VYRA should feel like:

```text
personal memory
+
context awareness
+
location awareness
+
current intelligence
+
reasoning
+
tools
+
personality
+
humor
+
research ability
+
initiative
+
continuity
+
controlled learning
```

She should know when to:

```text
speak
wait
research
remember
forget
interrupt
surprise
ask
act
```

The ultimate goal is not maximum automation.

The goal is **good judgment combined with continuity and personality**.

---

# 58. LAST UPDATED

CURRENT STEP

7.54 — Location/topic-aware intelligence selection

COMPLETED

7.45 — Entity & Topic Intelligence
7.46 — Entity-aware intelligence scoring
7.47 — RSS/Atom intelligence source adapter
7.48 — Source configuration/registry
7.49 — Source category configuration
7.50 — Verified real intelligence sources
7.51 — Intelligence priority engine
7.52 — Intelligence delivery policy
7.53 — Intelligence → InteractionEngine adapter

CURRENT ARCHITECTURE

Real intelligence source
→ IntelligenceStory
→ deduplication
→ entity extraction
→ entity-aware scoring
→ priority
→ delivery policy
→ InteractionEngine
→ SPEAK / WAIT