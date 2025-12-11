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


def find_org(as2_id):
    return org


def find_partner(as2_id):
    return partner


def find_org_partner(org_id, partner_id):
    return org, partner


def find_message(message_id, message_recipient):
    return None


def find_duplicate_message(message_id, message_recipient):
    return True


@pytest.mark.asyncio
async def test_phased_parsing_with_async_lookup():
    """Test the phased parsing approach with async lookup simulation"""

    # Build an As2 message to be transmitted to partner
    partner.sign = True
    partner.encrypt = True
    partner.mdn_mode = as2.SYNCHRONOUS_MDN
    out_message = as2.Message(org, partner)
    out_message.build(test_data)

    raw_out_message = out_message.headers_str + b"\r\n" + out_message.content

    # Phase 1: Extract headers (can be done anywhere)
    # Note: The message was built by org and sent to partner
    # So as2-from = org (some_organization), as2-to = partner (some_partner)
    # From the receiver's perspective:
    #   org_id (from as2-to) = the receiving organization = some_partner
    #   partner_id (from as2-from) = the sending partner = some_organization
    headers = as2.Message.extract_headers(raw_out_message)
    assert headers["org_id"] == "some_partner"  # as2-to
    assert headers["partner_id"] == "some_organization"  # as2-from
    assert headers["message_id"] is not None

    # Phase 2: Async lookup simulation (this is where you'd use await)
    async def async_lookup(org_id, partner_id):
        # Simulate async database lookup
        return org, partner

    receiver, sender = await async_lookup(headers["org_id"], headers["partner_id"])

    # Phase 3: Parse message with org/partner already set
    in_message = as2.Message(sender=sender, receiver=receiver)
    status, exception, mdn = in_message.parse_message(raw_out_message)

    assert status == "processed"
    assert in_message.signed
    assert in_message.encrypted

    # Also test MDN parsing with phased approach
    mdn_raw = mdn.headers_str + b"\r\n" + mdn.content

    # Phase 1: Extract MDN headers
    mdn_headers = as2.Mdn.extract_headers(mdn_raw)
    assert mdn_headers["orig_message_id"] == out_message.message_id

    # Phase 2: Async lookup for original message
    async def async_find_message(message_id, recipient):
        return out_message

    orig_msg = await async_find_message(
        mdn_headers["orig_message_id"], mdn_headers["orig_recipient"]
    )

    # Phase 3: Parse MDN
    out_mdn = as2.Mdn()
    mdn_status, detailed_status = out_mdn.parse_mdn(mdn_raw, orig_msg)
    assert mdn_status == "processed"


@pytest.mark.asyncio
async def test_phased_parsing_duplicate_check():
    """Test the phased parsing with duplicate detection"""

    partner.sign = True
    partner.encrypt = True
    partner.mdn_mode = as2.SYNCHRONOUS_MDN
    out_message = as2.Message(org, partner)
    out_message.build(test_data)

    raw_out_message = out_message.headers_str + b"\r\n" + out_message.content

    # Extract headers
    headers = as2.Message.extract_headers(raw_out_message)

    # Async lookup
    async def async_lookup(org_id, partner_id):
        return org, partner

    receiver, sender = await async_lookup(headers["org_id"], headers["partner_id"])

    # Async duplicate check
    async def async_check_duplicate(message_id, partner_id):
        return True  # Simulate duplicate found

    is_duplicate = await async_check_duplicate(
        headers["message_id"], headers["partner_id"]
    )

    # Parse message with duplicate flag
    in_message = as2.Message(sender=sender, receiver=receiver)
    status, exception, mdn = in_message.parse_message(
        raw_out_message, is_duplicate=is_duplicate
    )

    assert status == "processed/Warning"
    assert "duplicate-document" in exception[0].disposition_modifier


def test_sync_parse_still_works():
    """Test that the original sync parse() API still works"""

    partner.sign = True
    partner.encrypt = True
    partner.mdn_mode = as2.SYNCHRONOUS_MDN
    out_message = as2.Message(org, partner)
    out_message.build(test_data)

    raw_out_message = out_message.headers_str + b"\r\n" + out_message.content

    # Use original sync API with callbacks
    in_message = as2.Message()
    status, exception, mdn = in_message.parse(
        raw_out_message,
        find_org_cb=find_org,
        find_partner_cb=find_partner,
        find_message_cb=find_message,
    )

    assert status == "processed"
    assert in_message.signed
    assert in_message.encrypted


def test_sync_parse_with_partnership_callback():
    """Test sync parse with find_org_partner_cb"""

    partner.sign = False
    partner.encrypt = False
    partner.mdn_mode = None
    out_message = as2.Message(org, partner)
    out_message.build(test_data)

    raw_out_message = out_message.headers_str + b"\r\n" + out_message.content

    in_message = as2.Message()
    status, exception, mdn = in_message.parse(
        raw_out_message,
        find_org_partner_cb=find_org_partner,
    )

    assert status == "processed"
    assert in_message.content == test_data


def test_sync_parse_duplicate_message():
    """Test sync parse with duplicate message detection"""

    partner.sign = True
    partner.encrypt = True
    partner.mdn_mode = as2.SYNCHRONOUS_MDN
    out_message = as2.Message(org, partner)
    out_message.build(test_data)

    raw_out_message = out_message.headers_str + b"\r\n" + out_message.content

    in_message = as2.Message()
    status, exception, mdn = in_message.parse(
        raw_out_message,
        find_org_cb=find_org,
        find_partner_cb=find_partner,
        find_message_cb=find_duplicate_message,
    )

    assert status == "processed/Warning"
    assert "duplicate-document" in exception[0].disposition_modifier


def test_sync_mdn_parse():
    """Test sync MDN parse"""

    partner.sign = True
    partner.encrypt = True
    partner.mdn_mode = as2.SYNCHRONOUS_MDN
    out_message = as2.Message(org, partner)
    out_message.build(test_data)

    raw_out_message = out_message.headers_str + b"\r\n" + out_message.content

    in_message = as2.Message()
    status, exception, mdn = in_message.parse(
        raw_out_message,
        find_org_cb=find_org,
        find_partner_cb=find_partner,
    )

    def find_orig_message(message_id, recipient):
        return out_message

    out_mdn = as2.Mdn()
    mdn_status, detailed_status = out_mdn.parse(
        mdn.headers_str + b"\r\n" + mdn.content,
        find_message_cb=find_orig_message,
    )
    assert mdn_status == "processed"
