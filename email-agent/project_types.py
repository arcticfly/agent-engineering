from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Email(BaseModel):
    message_id: str
    date: str  # ISO 8601 string 'YYYY-MM-DD HH:MM:SS'
    subject: Optional[str] = None
    from_address: Optional[str] = None
    to_addresses: List[str] = []  # Populated from recipients table
    cc_addresses: List[str] = []  # Populated from recipients table
    bcc_addresses: List[str] = []  # Populated from recipients table
    body: Optional[str] = None
    file_name: Optional[str] = None


class Scenario(BaseModel):
    id: int
    question: str
    answer: str
    message_ids: List[str]  # message_ids (strings) of referenced emails
    how_realistic: float
    inbox_address: str
    query_date: str
    split: Literal["train", "test"]


class RunConfig(BaseModel):
    num_epochs: int = 1
    groups_per_step: int = 12
    validation_frequency: int = 10
    validation_num_scenarios: int = 100
    training_num_scenarios: int = 1000
    rollouts_per_group: int = 4
    learning_rate: float = 1.2e-5
