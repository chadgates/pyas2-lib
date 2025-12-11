import os

import pytest

from pyas2lib import as2
from pyas2lib.tests import TEST_DIR

with open(os.path.join(TEST_DIR, "payload.txt"), "rb") as fp:
    test_data = fp.read()

with open(os.path.join(TEST_DIR, "cert_test.p12"), "rb") as fp:
    private_key = fp.read()

with open(os.path.join(TEST_DIR, "cert_test_public.pem"), "rb") as fp:
    public_key = fp.read()

org = as2.Organization(
    as2_name="some_organization",
    sign_key=private_key,
    sign_key_pass="test",
    decrypt_key=private_key,
    decrypt_key_pass="test",
)
partner = as2.Partner(
    as2_name="some_partner",
    verify_cert=public_key,
    encrypt_cert=public_key,
)


async def afind_org(headers):
    return org


async def afind_partner(headers):
    return partner


async def afind_duplicate_message(message_id, message_recipient):
    return True


async def afind_org_partner(as2_org, as2_partner):
    return org, partner


# Sync callbacks for testing sync callbacks in async context
def sync_find_org(headers):
    return org


def sync_find_partner(headers):
    return partner


def sync_find_message(message_id, message_recipient):
    return None


def sync_find_org_partner(as2_org, as2_partner):
    return org, partner


@pytest.mark.asyncio
async def test_async_callbacks_with_duplicate_message():
    """Test case where async callbacks are used and a duplicate message is sent to the partner"""

    # Build an As2 message to be transmitted to partner
    partner.sign = True
    partner.encrypt = True
    partner.mdn_mode = as2.SYNCHRONOUS_MDN
    out_message = as2.Message(org, partner)
    out_message.build(test_data)

    async def afind_message(message_id, message_recipient):
        return out_message

    # Parse the generated AS2 message as the partner
    raw_out_message = out_message.headers_str + b"\r\n" + out_message.content
    in_message = as2.Message()
    _, _, mdn = await in_message.aparse(
        raw_out_message,
        find_org_cb=afind_org,
        find_partner_cb=afind_partner,
        find_message_cb=afind_duplicate_message,
    )

    out_mdn = as2.Mdn()
    status, detailed_status = await out_mdn.aparse(
        mdn.headers_str + b"\r\n" + mdn.content,
        find_message_cb=afind_message,
    )
    assert status == "processed/Warning"
    assert detailed_status == "duplicate-document"


@pytest.mark.asyncio
async def test_async_partnership():
    """Test Async Partnership callback"""

    # Build an As2 message to be transmitted to partner
    out_message = as2.Message(org, partner)
    out_message.build(test_data)
    raw_out_message = out_message.headers_str + b"\r\n" + out_message.content

    # Parse the generated AS2 message as the partner
    in_message = as2.Message()
    status, _, _ = await in_message.aparse(
        raw_out_message, find_org_partner_cb=afind_org_partner
    )

    # Compare contents of the input and output messages
    assert status == "processed"


@pytest.mark.asyncio
async def test_runtime_error():
    """Test to get Runtime error when calling parse instead of aparse from Async Context"""

    with pytest.raises(
        RuntimeError,
        match="Cannot run synchronous parse within an already running event loop, use aparse.",
    ):
        out_message = as2.Message(org, partner)
        out_message.build(test_data)
        raw_out_message = out_message.headers_str + b"\r\n" + out_message.content

        in_message = as2.Message()
        status, _, _ = in_message.parse(
            raw_out_message, find_org_partner_cb=afind_org_partner
        )

    with pytest.raises(
        RuntimeError,
        match="Cannot run synchronous parse within an already running event loop, use aparse.",
    ):
        partner.sign = True
        partner.encrypt = True
        partner.mdn_mode = as2.SYNCHRONOUS_MDN
        out_message = as2.Message(org, partner)
        out_message.build(test_data)

        # Parse the generated AS2 message as the partner
        raw_out_message = out_message.headers_str + b"\r\n" + out_message.content
        in_message = as2.Message()
        _, _, mdn = await in_message.aparse(
            raw_out_message,
            find_org_cb=afind_org,
            find_partner_cb=afind_partner,
            find_message_cb=afind_duplicate_message,
        )

        out_mdn = as2.Mdn()
        _, _ = out_mdn.parse(
            mdn.headers_str + b"\r\n" + mdn.content,
            find_message_cb=afind_duplicate_message,
        )


@pytest.mark.asyncio
async def test_sync_callbacks_in_async_context():
    """Test that sync callbacks work correctly when called from aparse (async context)"""

    # Build an As2 message to be transmitted to partner
    partner.sign = True
    partner.encrypt = True
    partner.mdn_mode = as2.SYNCHRONOUS_MDN
    out_message = as2.Message(org, partner)
    out_message.build(test_data)

    # Parse the generated AS2 message as the partner using SYNC callbacks in async context
    raw_out_message = out_message.headers_str + b"\r\n" + out_message.content
    in_message = as2.Message()
    status, _, mdn = await in_message.aparse(
        raw_out_message,
        find_org_cb=sync_find_org,
        find_partner_cb=sync_find_partner,
        find_message_cb=sync_find_message,
    )

    assert status == "processed"
    assert in_message.signed
    assert in_message.encrypted

    # Also test MDN parsing with sync callback
    def sync_find_orig_message(message_id, message_recipient):
        return out_message

    out_mdn = as2.Mdn()
    mdn_status, detailed_status = await out_mdn.aparse(
        mdn.headers_str + b"\r\n" + mdn.content,
        find_message_cb=sync_find_orig_message,
    )
    assert mdn_status == "processed"


@pytest.mark.asyncio
async def test_sync_partnership_callback_in_async_context():
    """Test that sync find_org_partner_cb works correctly when called from aparse"""

    # Build an As2 message to be transmitted to partner
    partner.sign = False
    partner.encrypt = False
    partner.mdn_mode = None
    out_message = as2.Message(org, partner)
    out_message.build(test_data)
    raw_out_message = out_message.headers_str + b"\r\n" + out_message.content

    # Parse the generated AS2 message using SYNC callback in async context
    in_message = as2.Message()
    status, _, _ = await in_message.aparse(
        raw_out_message, find_org_partner_cb=sync_find_org_partner
    )

    # Compare contents of the input and output messages
    assert status == "processed"
    assert in_message.content == test_data
