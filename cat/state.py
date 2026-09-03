from enum import Enum


class CatState(Enum):
    IDLE = "idle"
    SLEEP = "sleep"
    WAKE = "wake"
    STARTLED = "startled"
    LOOK_AT_USER = "look_at_user"
    LOOK = "look"
    WALK = "walk"
    RUN = "run"
    HAPPY = "happy"
    ANGRY = "angry"
    SAD = "sad"
    EXCITED = "excited"
    PLAY = "play"
    DRAGGED = "dragged"
    DRAG = "drag"
    PET = "pet"
