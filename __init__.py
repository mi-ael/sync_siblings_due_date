import threading
import time
from typing import List, Optional
from anki.notes import Note
from anki.cards import Card
from anki import hooks
from anki.consts import QUEUE_TYPE_DAY_LEARN_RELEARN, QUEUE_TYPE_REV
from anki.scheduler.base import SchedulerBase
from aqt import mw
from aqt.main import AnkiQt

def debug_print(output :str) -> None:
  print(output)

def find_lowest_sibling_due_date(siblings :List[Card]) -> int:
  return min([s.due for s in siblings])

currently_flushing :bool = False

def sync_all_due_dates() -> None:
  global currently_flushing
  time.sleep(10)
  note_ids = mw.col.find_notes("is:due")
  for note_id in note_ids:
    note = mw.col.getNote(note_id)
    siblings :List[Card] = note.cards() 
    siblings_in_right_queue :List[Card] = [s for s in siblings if s.queue in (QUEUE_TYPE_DAY_LEARN_RELEARN, QUEUE_TYPE_REV)]
    lowest_sibling_due_date :int = find_lowest_sibling_due_date(siblings_in_right_queue)
    currently_flushing = True
    #if len(siblings_in_right_queue) > 1:
      #import pdb; pdb.set_trace()
    for s in siblings_in_right_queue:
      if s.due != lowest_sibling_due_date:
        s.due = lowest_sibling_due_date
        s.flush()
        print(f"SYNC_SIBLING_DUE_DATE: synced sibling due dates: {s.question()}")
    currently_flushing = False

# hack to set all existing cards to correct due dates
#threading.Thread(target=sync_all_due_dates).start()

def myfunc(card: Card) -> None:
  global currently_flushing
  if currently_flushing: return
  if card.queue not in (QUEUE_TYPE_DAY_LEARN_RELEARN,QUEUE_TYPE_REV): return
  note :Note = card.note()
  scheduler :SchedulerBase = card.col.sched
  if card.due <= scheduler.today: return
  siblings :List[Card] = note.cards()
  for i,s in enumerate(siblings):
    if s.id == card.id:
      siblings[i] = card
  siblings_in_same_deck :List[Card] = [s for s in siblings if s.did == card.did]
  siblings_in_right_queue :List[Card] = [s for s in siblings_in_same_deck if s.queue in (QUEUE_TYPE_DAY_LEARN_RELEARN, QUEUE_TYPE_REV) and s.due > scheduler.today]
  assert len(siblings_in_right_queue) > 0
  lowest_sibling_due_date :int = find_lowest_sibling_due_date(siblings_in_right_queue)
  min_interval :int = min([s.ivl for s in siblings_in_right_queue])
  currently_flushing = True
  #import pdb; pdb.set_trace()
  for s in siblings_in_right_queue:
    if s.due != lowest_sibling_due_date:
      s.due = lowest_sibling_due_date
      s.ivl = min_interval
      if s.id != card.id:
        s.flush()
        print("SYNC_SIBLING_DUE_DATE: synced sibling due date")
  currently_flushing = False

hooks.card_will_flush.append(myfunc)
