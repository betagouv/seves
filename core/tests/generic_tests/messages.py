from playwright.sync_api import Page, expect

from core.factories import ContactAgentFactory
from core.models import Message
from core.pages import WithMessagePage


def generic_test_can_add_and_see_message_without_document(live_server, page: Page, choice_js_fill, object):
    active_contact = ContactAgentFactory(with_active_agent=True).agent

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = WithMessagePage(page)
    message_page.new_message()
    message_page.pick_recipient(active_contact, choice_js_fill)
    expect(message_page.message_form_title).to_have_text("message")

    message_page.message_title.fill("Title of the message")
    message_page.message_content.fill("My content \n with a line return")
    message_page.submit_message()

    page.wait_for_url(f"**{object.get_absolute_url()}#tabpanel-messages-panel")

    assert message_page.message_sender_in_table() == "Structure Test"
    assert message_page.message_recipient_in_table() == str(active_contact)
    assert message_page.message_title_in_table() == "Title of the message"
    assert message_page.message_type_in_table() == "Message"
    message_page.open_message()

    expect(message_page.message_title_in_sidebar).to_be_visible()
    assert "My content <br> with a line return" in message_page.message_content_in_sidebar.inner_html()
    assert object.messages.get().status == Message.Status.FINALISE
