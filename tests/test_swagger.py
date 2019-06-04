#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from pimsclient.client import Pseudonym, Identifier
from pimsclient.swagger import KeyFile, User, KeyFiles
from tests.factories import UserFactory, RequestsMock, KeyFileFactory, RequestsMockResponseExamples, PseudonymFactory


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
    mock_pims_session.session.set_response_tuple(RequestsMockResponseExamples.KEYFILES_FORUSER_RESPONSE)
    entrypoint = KeyFiles(mock_pims_session)

    keyfiles = entrypoint.get_all(user=UserFactory())
    assert len(keyfiles) == 1
    keyfiles[0].name == 'string'

    mock_pims_session.session.set_response_tuple(RequestsMockResponseExamples.KEYFILES_RESPONSE)
    keyfile = entrypoint.get(key=0)
    assert keyfile.name == 'string'

    mock_pims_session.session.set_response_tuple(RequestsMockResponseExamples.KEYFILES_PSEUDONYMS_POST_RESPONSE)
    keyfile = entrypoint.get(key=0)
    assert keyfile.name == 'string'


def test_keyfiles_pseudonymize(mock_pims_session):
    """Get a pseudonym, mock server response"""
    mock_pims_session.session.set_response_tuple(RequestsMockResponseExamples.KEYFILES_PSEUDONYMS_POST_RESPONSE)
    entrypoint = KeyFiles(mock_pims_session)
    pseudonyms = entrypoint.pseudonymize(keyfile=KeyFileFactory(),
                                         identifiers=[Identifier(value='Jack de Boer', source='Test'),
                                                      Identifier(value='Chris van Os', source='Test')])
    assert len(pseudonyms) == 2
    assert pseudonyms[0].pseudonym.value == '63bf2309-d280-44d0-914b-a74a25dfc56d'


def test_keyfiles_reidentify(mock_pims_session):
    mock_pims_session.session.set_response_tuple(RequestsMockResponseExamples.KEYFILES_PSEUDONYMS_REIDENTIFY_RESPONSE)
    entrypoint = KeyFiles(mock_pims_session)

    keys = entrypoint.reidentify(key_file=KeyFileFactory(),
                                 pseudonyms=[PseudonymFactory(), PseudonymFactory()])

    assert len(keys) == 2
    assert keys[0].identifier.source == 'sjoerd_zelf'






