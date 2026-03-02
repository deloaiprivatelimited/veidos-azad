import vertexai
from vertexai.generative_models import GenerativeModel,Part

# Initialize
vertexai.init(project="lively-aloe-411504", location="us-central1")

model = GenerativeModel("gemini-2.5-pro")



# Read local PDF file
with open("class 8 part1\chapter1\chapter1.pdf", "rb") as f:
    pdf_bytes = f.read()

# Create PDF part (this includes text + images inside PDF)
pdf_part = Part.from_data(
    data=pdf_bytes,
    mime_type="application/pdf"
)

# Ask question about the PDF
response = model.generate_content([
    pdf_part,
    "Summarize this document and explain any charts or images it contains."
])

# Print result
print(response.text)