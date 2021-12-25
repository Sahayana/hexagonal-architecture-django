from http import HTTPStatus
from uuid import UUID, uuid4

from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from myapp.application.adapter.api.http.article_vote_view import ArticleVoteView
from myapp.application.domain.model.identifier.article_id import ArticleId
from myapp.application.domain.model.identifier.user_id import UserId
from myapp.application.domain.model.vote import Vote
from myapp.application.domain.model.vote_for_article_result import (
    AlreadyVotedResult,
    InsufficientKarmaResult,
    SuccessfullyVotedResult,
    VoteForArticleResult
)
from myapp.application.ports.api.vote_for_article_use_case import (
    VoteForArticleCommand,
    VoteForArticleUseCase
)


def test_post_article_vote(
    arf: APIRequestFactory,
    user_id: UserId,
    article_id: ArticleId
):
    vote_for_article_use_case_mock = VoteForArticleUseCaseMock(
        returned_result=SuccessfullyVotedResult(
            user_id=user_id,
            article_id=article_id,
            vote=Vote.DOWN
        )
    )

    article_vote_view = ArticleVoteView.as_view(
        vote_for_article_use_case=vote_for_article_use_case_mock
    )

    response: Response = article_vote_view(
        arf.post(
            '/article_vote',
            {
                'user_id': user_id,
                'article_id': article_id,
                'vote': Vote.DOWN.value
            },
            format='json'
        )
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.data == {
        'article_id': str(article_id),
        'user_id': str(user_id),
        'vote': 'DOWN'
    }


def test_post_article_vote_with_malformed_data_returns_bad_request(
    arf: APIRequestFactory
):
    vote_for_article_use_case_mock = VoteForArticleUseCaseMock()

    article_vote_view = ArticleVoteView.as_view(
        vote_for_article_use_case=vote_for_article_use_case_mock
    )

    response: Response = article_vote_view(
        arf.post(
            '/article_vote',
            {
                'user_id': str(uuid4()),
                'article_id': str(uuid4())
            },
            format='json'
        )
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_article_vote_with_insufficient_karma_returns_bad_request(
    arf: APIRequestFactory,
    user_id: UserId,
    article_id: UUID
):
    vote_for_article_use_case_mock = VoteForArticleUseCaseMock(
        returned_result=InsufficientKarmaResult(
            user_id=user_id
        )
    )

    article_vote_view = ArticleVoteView.as_view(
        vote_for_article_use_case=vote_for_article_use_case_mock
    )

    response: Response = article_vote_view(
        arf.post(
            '/article_vote',
            {
                'user_id': user_id,
                'article_id': article_id,
                'vote': Vote.UP.value
            },
            format='json'
        )
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.data == {
        'status': 400,
        'detail': f"User {user_id} does not have enough karma to vote for an article",
        'title': "Cannot vote for an article"
    }


def test_post_article_vote_with_same_user_and_article_id_twice_returns_conflict(
    arf: APIRequestFactory,
    user_id: UserId,
    article_id: ArticleId
):
    vote_for_article_use_case_mock = VoteForArticleUseCaseMock(
        returned_result=AlreadyVotedResult(
            user_id=user_id,
            article_id=article_id
        )
    )

    article_vote_view = ArticleVoteView.as_view(
        vote_for_article_use_case=vote_for_article_use_case_mock
    )

    response: Response = article_vote_view(
        arf.post(
            '/article_vote',
            {
                'user_id': user_id,
                'article_id': article_id,
                'vote': Vote.UP.value
            },
            format='json'
        )
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.data == {
        'status': 409,
        'detail': (f"User \"{user_id}\" has already voted"
                   f" for article \"{article_id}\""),
        'title': "Cannot vote for an article"
    }


class VoteForArticleUseCaseMock(VoteForArticleUseCase):
    called_with_command = None

    def __init__(
        self,
        returned_result: VoteForArticleResult = None
    ):
        if returned_result is None:
            returned_result = SuccessfullyVotedResult(
                user_id=UserId(uuid4()),
                article_id=ArticleId(uuid4()),
                vote=Vote.UP
            )
        self._returned_result = returned_result

    def vote_for_article(self, command: VoteForArticleCommand) -> VoteForArticleResult:
        self.called_with_command = command
        return self._returned_result
