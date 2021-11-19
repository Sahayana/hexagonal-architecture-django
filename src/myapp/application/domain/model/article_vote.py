from dataclasses import dataclass, field
from uuid import UUID, uuid4

from myapp.application.domain.model.identifier.user_id import UserId
from myapp.application.domain.model.vote import Vote


@dataclass
class ArticleVote:
    user_id: UserId
    article_id: UUID
    vote: Vote
    id: UUID = field(default_factory=uuid4)
