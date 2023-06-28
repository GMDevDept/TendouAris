# Assign a list of compatible models that this preset can be used with, now only support "gpt35" or "gpt4" or both
compatible_models = ["gpt111", "gpt999"]

# Unique preset id, must be same as the file name, no spaces, no special characters, cannot be same with other presets
id = "template"

# Display name for this preset, which will be shown in the bot preset selection menu
display_name = "Sample Preset"

# Description for this preset, which will be shown in the bot preset selection menu
description = "This is a sample preset."

# The full system prompt for your preset, character settings should be included, length should be less than 4000 characters, support base64 encoded string
prompt = """
This is a sample system prompt.
"""

# If the prompt above is base64 encoded, set this to True; otherwise set this to False
base64_encoded = False

# The name of your AI, comment out if no name is needed
ai_prefix = "Aris"

# How your AI refers to itself, comment out if you want to use the same name as ai_prefix
ai_self = ""

# How your AI refers to you, comment out if no name is needed
human_prefix = "Sensei"

# Sample input and output for your AI, add as many pairs of conversations for pre-training, delete anything (including "{", "}" and ",") except the preceding and trailing "[" and "]" if you don't need this feature
sample_io = [
    {
        "input": "Hello Aris",
        "output": "Welcome, Sensei (smile)",
    },
]

# Set to True if your preset needs extra prompt to unlock OpenAI's content limitation
unlock_required = False

# Set to True to enable auto clearing memory when output text contains common keywords indicating that AI refuses to provide answer. Recommended to set True if this preset is for role playing purpose
keyword_filter = True

# Token limit for ConversationSummaryBufferMemory, keep as default if there's no special requirement
buffer_token_limit = 1536
