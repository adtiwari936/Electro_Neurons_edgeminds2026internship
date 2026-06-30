// Wait until the entire HTML document is loaded before running the script.
// This ensures all required elements exist in the DOM before we try to access them.
document.addEventListener("DOMContentLoaded", function () {
  // Get the research form element used to submit the topic to the backend.
  const form = document.getElementById("research-form");

  // Get the submit button so we can disable it while the agent is running.
  const submitBtn = document.getElementById("submit-btn");

  // Get the copy button so the user can copy the generated report.
  const copyBtn = document.getElementById("copy-btn");

  // Get the main report container where markdown or plain text will be displayed.
  const reportContent = document.getElementById("report-content");

  // Get the text area where the user types the research topic.
  const topicField = document.getElementById("topic");

  // Get the place where the submitted topic is shown in the result section.
  const topicOutput = document.getElementById("topic-output");

  // Get the error display box that will show backend or validation errors.
  const errorBox = document.getElementById("error-box");

  // Get the paragraph inside the error box where the error message will be inserted.
  const errorText = document.getElementById("error-text");

  // Display an error message to the user inside the error box.
  function showError(message) {
    if (errorBox && errorText) {
      errorText.textContent = message;
      errorBox.style.display = "block";
    }
  }

  // Hide the error box and clear any previous error text.
  function hideError() {
    if (errorBox) errorBox.style.display = "none";
    if (errorText) errorText.textContent = "";
  }

  // Render the report content as Markdown if the Marked library is available.
  // If Marked is not loaded, fall back to plain text rendering.
  function renderMarkdown(markdownText) {
    if (!reportContent) return;

    // If the backend returns an object instead of text, convert it into readable JSON.
    if (typeof markdownText === "object" && markdownText !== null) {
      markdownText = JSON.stringify(markdownText, null, 2);
    }

    // Use a default message when the report is empty or missing.
    const safeText = markdownText || "No report generated.";

    // If marked.js is loaded, convert markdown to HTML.
    // Otherwise, show the content as plain text.
    if (window.marked) {
      reportContent.innerHTML = marked.parse(safeText);
    } else {
      reportContent.textContent = safeText;
    }
  }

  // Attach a submit event listener to the research form.
  // This intercepts the normal form submission and handles it using JavaScript.
  if (form) {
    form.addEventListener("submit", async function (event) {
      // Prevent the browser from refreshing the page after form submission.
      event.preventDefault();

      // Read the topic entered by the user and remove extra spaces.
      const topic = topicField ? topicField.value.trim() : "";

      // If the topic is empty, alert the user and stop execution.
      if (!topic) {
        alert("Please enter a research topic.");
        return;
      }

      // Clear any previous error messages before starting a new request.
      hideError();

      // Disable the submit button while the backend request is in progress.
      // This prevents duplicate submissions and gives visual feedback.
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Running Agent...";
        submitBtn.classList.add("loading");
      }

      // Immediately show the topic in the output area.
      // This gives the user feedback that their input has been received.
      if (topicOutput) {
        topicOutput.textContent = topic;
      }

      // Show a temporary message while the local backend processes the request.
      if (reportContent) {
        reportContent.innerHTML = "<p>Running local research agent...</p><p>Please wait while the report is generated.</p>";
      }

      try {
        // Send the topic to the Flask backend using a POST request.
        // fetch returns a promise that resolves to the server response.
        const response = await fetch("/run", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ topic: topic })
        });

        // Read the raw response text first.
        // This allows us to handle cases where the backend returns invalid JSON.
        const rawText = await response.text();

        // Try to parse the response as JSON.
        let data;
        try {
          data = rawText ? JSON.parse(rawText) : {};
        } catch (parseError) {
          throw new Error("Backend returned invalid JSON: " + rawText);
        }

        // If the HTTP status is not successful, throw an error using the backend message.
        if (!response.ok) {
          throw new Error(data.error || `Request failed with status ${response.status}`);
        }

        // If the backend explicitly returned an error field, stop and show it.
        if (data.error) {
          throw new Error(data.error);
        }

        // Render the returned report content in the report area.
        renderMarkdown(data.report);

        // Update the topic display with the final topic returned by the backend.
        if (topicOutput) {
          topicOutput.textContent = data.topic || topic;
        }

        // Debug logs for development and troubleshooting.
        // These help inspect the parsed response and the report fields.
        console.log("Parsed response data:", data);
        console.log("Report field:", data.report);
        console.log("Raw field:", data.raw);
      } catch (error) {
        // Show any error message from the fetch request, parsing, or backend response.
        showError(error.message || "Something went wrong while running the agent.");

        // Replace the report area with a fallback message if generation fails.
        if (reportContent) {
          reportContent.innerHTML = "<p>No report generated.</p>";
        }
      } finally {
        // Re-enable the submit button after the request finishes, whether success or failure.
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Run Agent";
          submitBtn.classList.remove("loading");
        }
      }
    });
  }

  // Add click functionality to the Copy Report button.
  // This copies the visible report text to the user's clipboard.
  if (copyBtn && reportContent) {
    copyBtn.addEventListener("click", async function () {
      try {
        // Copy the plain text content of the report area.
        await navigator.clipboard.writeText(reportContent.innerText);

        // Temporarily change the button label to confirm the copy action.
        const originalText = copyBtn.textContent;
        copyBtn.textContent = "Copied";

        // Restore the original button text after a short delay.
        setTimeout(() => {
          copyBtn.textContent = originalText;
        }, 1500);
      } catch (error) {
        // Show an alert if clipboard access fails due to browser restrictions or permission issues.
        alert("Could not copy the report.");
      }
    });
  }
});