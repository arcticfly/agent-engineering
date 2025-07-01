# %%

from email_search_tools import search_emails, read_email

# 1️⃣  Run a search
hits = search_emails(
    inbox="louise.kitchen@enron.com",
    keywords=["meeting", "schedule"],
    max_results=3,
)

print("SEARCH RESULTS:")
for h in hits:
    print(h)
