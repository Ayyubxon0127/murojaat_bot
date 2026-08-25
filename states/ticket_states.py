# -*- coding: utf-8 -*-
from aiogram.fsm.state import State, StatesGroup


class NewTicket(StatesGroup):
    department = State()
    category = State()
    description = State()
    photos = State()
    comment = State()
    preview = State()
    edit_description = State()


class ResolveTicket(StatesGroup):
    waiting_comment = State()


class AddComment(StatesGroup):
    waiting_comment = State()


class UserComment(StatesGroup):
    waiting_comment = State()
