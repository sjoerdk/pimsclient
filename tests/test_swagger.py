#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pimsclient.swagger import KeyFile, User, KeyFiles, Users, Identifier
from tests.factories import (
    UserFactory,
    KeyFileFactory,
    RequestsMockResponseExamples,
    PseudonymFactory,
    IdentifierFactory,
)


def test_swagger_user():
    user = UserFactory()
    as_dict = user.to_dict()

    reconstructed = User.from_dict(as_dict)
    assert reconstructed.email == user.email
    assert reconstructed.name == user.name
    assert reconstructed.key == user.key


def test_swagger_keyfile():
    keyfile = KeyFileFactory()
    as_dict = keyfile.to_dict()

    reconstructed = KeyFile.from_dict(as_dict)
    assert reconstructed.pseudonym_template == keyfile.pseudonym_template
    assert reconstructed.description == keyfile.description
    assert reconstructed.name == keyfile.name
    assert reconstructed.key == keyfile.key


def test_keyfiles_entrypoint(mock_pims_session):
    """Get some object from entrypoint, server is mocked and returning mocked responses

    """
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.KEYFILES_FORUSER_RESPONSE
    )
    entrypoint = KeyFiles(mock_pims_session)

    keyfiles = entrypoint.get_all(user=UserFactory())
    assert len(keyfiles) == 1
    keyfiles[0].name == "string"

    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.KEYFILES_RESPONSE
    )
    keyfile = entrypoint.get(key=0)
    assert keyfile.name == "string"


def test_keyfiles_pseudonymize(mock_pims_session):
    """Get a pseudonym, mock server response"""
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.KEYFILES_PSEUDONYMS_POST_RESPONSE
    )
    entrypoint = KeyFiles(mock_pims_session)
    pseudonyms = entrypoint.pseudonymize_legacy(
        key_file=KeyFileFactory(),
        identifiers=[
            Identifier(value="Jack de Boer", source="Test"),
            Identifier(value="Chris van Os", source="Test"),
        ],
    )
    assert len(pseudonyms) == 2
    assert pseudonyms[0].pseudonym.value == "63bf2309-d280-44d0-914b-a74a25dfc56d"


def test_keyfiles_pseudonymize_different_sources(mock_pims_session):
    """Get a pseudonym, mock server response"""
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.KEYFILES_PSEUDONYMS_POST_RESPONSE
    )
    entrypoint = KeyFiles(mock_pims_session)
    pseudonyms = entrypoint.pseudonymize_legacy(
        key_file=KeyFileFactory(),
        identifiers=[
            Identifier(value="Jack de Boer", source="Test"),
            Identifier(value="Chris van Os", source="Test"),
            Identifier(value="Sarah Toh", source="Test_2"),
        ],
    )
    assert len(pseudonyms) == 3


def test_keyfiles_reidentify(mock_pims_session):
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.KEYFILES_PSEUDONYMS_REIDENTIFY_RESPONSE
    )
    entrypoint = KeyFiles(mock_pims_session)

    keys = entrypoint.reidentify(
        key_file=KeyFileFactory(), pseudonyms=[PseudonymFactory(), PseudonymFactory()]
    )

    assert len(keys) == 2
    assert keys[0].identifier.source == "sjoerd_zelf"


def test_keyfiles_get_users(mock_pims_session):
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.GET_USERS_FOR_KEYFILE_RESPONSE
    )
    entrypoint = KeyFiles(mock_pims_session)

    users = entrypoint.get_users(key_file=KeyFileFactory())

    assert len(users) == 2
    assert users[1].key == 22


def test_users_get_by_id(mock_pims_session):
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.GET_USER_BY_ID_RESPONSE
    )
    entrypoint = Users(mock_pims_session)

    user = entrypoint.get(key=1)

    assert user.name == 'umcn\\SVC01234'



def test_string_reprs():
    """Getting coverage up a bit
    """
    all_strings = (
        f"{UserFactory()}{KeyFileFactory()}{PseudonymFactory()}{IdentifierFactory()}"
    )
    assert all_strings != ""  # Or actually, assert nothing crashed
