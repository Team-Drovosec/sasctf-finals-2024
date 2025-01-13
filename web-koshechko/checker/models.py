
from dataclasses import dataclass
from typing import List


@dataclass 
class User:
	name: str
	desc: str
	rank: int

@dataclass 
class Koshechko:
	name: str
	owner: str
	text: str
	rank: int
	score: int
	shared_with: List[str]


@dataclass 
class KoshechkoTop:
	name: str
	rank: str
	score: str

@dataclass 
class UserTop:
	name: str
	rank: str
	score: str

