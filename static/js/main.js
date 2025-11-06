document.addEventListener("DOMContentLoaded", () => {
  // Add fade-in animation to table rows
  const tableRows = document.querySelectorAll("tbody tr");
  tableRows.forEach((row, index) => {
    row.style.opacity = "0";
    row.style.transform = "translateY(20px)";
    setTimeout(() => {
      row.style.transition = "opacity 0.5s ease, transform 0.5s ease";
      row.style.opacity = "1";
      row.style.transform = "translateY(0)";
    }, index * 50);
  });

  // Add hover effect to upload zone
  const uploadZone = document.querySelector(".upload-zone");
  if (uploadZone) {
    uploadZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      uploadZone.style.borderColor = "var(--primary-dark)";
      uploadZone.style.background = "linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%)";
      uploadZone.style.transform = "scale(1.02)";
    });

    uploadZone.addEventListener("dragleave", () => {
      uploadZone.style.borderColor = "var(--primary-color)";
      uploadZone.style.background = "linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)";
      uploadZone.style.transform = "scale(1)";
    });

    uploadZone.addEventListener("drop", (e) => {
      e.preventDefault();
      uploadZone.style.borderColor = "var(--primary-color)";
      uploadZone.style.background = "linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)";
      uploadZone.style.transform = "scale(1)";
    });
  }

  // Smooth scroll for alerts
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach(alert => {
    alert.style.animation = "fadeIn 0.5s ease-out";
  });

  // Initialize Flatpickr for all date inputs with English format
  // Store Flatpickr instances for later use
  const flatpickrInstances = {};
  const dateInputs = document.querySelectorAll('input[type="date"]');
  dateInputs.forEach(input => {
    const fp = flatpickr(input, {
      dateFormat: "Y-m-d",
      altInput: true,
      altFormat: "F j, Y", // English format: "November 5, 2025"
      locale: "en",
      allowInput: true,
    });
    // Store instance by input ID for OCR to use
    if (input.id) {
      flatpickrInstances[input.id] = fp;
    }
  });

  // Customize file input buttons to show English text
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(fileInput => {
    // Create wrapper for custom button
    const wrapper = document.createElement('div');
    wrapper.className = 'custom-file-input-wrapper position-relative';

    // Create custom button
    const customButton = document.createElement('button');
    customButton.type = 'button';
    customButton.className = 'btn btn-outline-primary w-100';
    customButton.innerHTML = '<i class="fas fa-upload me-2"></i>Choose File';

    // Create filename display
    const filenameDisplay = document.createElement('div');
    filenameDisplay.className = 'mt-2 text-muted small';
    filenameDisplay.textContent = 'No file selected';

    // Hide original input
    fileInput.style.position = 'absolute';
    fileInput.style.opacity = '0';
    fileInput.style.width = '100%';
    fileInput.style.height = '100%';
    fileInput.style.top = '0';
    fileInput.style.left = '0';
    fileInput.style.cursor = 'pointer';

    // Insert custom button before input
    fileInput.parentNode.insertBefore(wrapper, fileInput);
    wrapper.appendChild(customButton);
    wrapper.appendChild(fileInput);
    wrapper.appendChild(filenameDisplay);

    // Update display when file is selected
    fileInput.addEventListener('change', function() {
      if (this.files && this.files.length > 0) {
        const fileName = this.files[0].name;
        filenameDisplay.textContent = `Selected: ${fileName}`;
        filenameDisplay.className = 'mt-2 text-success small';
        customButton.innerHTML = `<i class="fas fa-check-circle me-2"></i>${fileName}`;
        customButton.className = 'btn btn-success w-100';
      } else {
        filenameDisplay.textContent = 'No file selected';
        filenameDisplay.className = 'mt-2 text-muted small';
        customButton.innerHTML = '<i class="fas fa-upload me-2"></i>Choose File';
        customButton.className = 'btn btn-outline-primary w-100';
      }
    });

    // Trigger file input when custom button is clicked
    customButton.addEventListener('click', () => {
      fileInput.click();
    });
  });

  // OCR functionality
  const fileInput = document.getElementById("invoiceFile");
  const statusBox = document.getElementById("ocr-status");

  if (!fileInput || !statusBox) {
    return;
  }

  const fieldMap = {
    invoice_number: document.getElementById("invoiceNumber"),
    invoice_date: document.getElementById("invoiceDate"),
    company_name: document.getElementById("companyName"),
    total_amount: document.getElementById("totalAmount"),
  };

  const showStatus = (message, type) => {
    statusBox.textContent = message;
    statusBox.classList.remove(
      "d-none",
      "alert-info",
      "alert-success",
      "alert-danger",
      "alert-warning"
    );
    statusBox.classList.add(`alert-${type}`);
  };

  const hideStatus = () => {
    statusBox.textContent = "";
    statusBox.classList.add("d-none");
    statusBox.classList.remove("alert-info", "alert-success", "alert-danger", "alert-warning");
  };

  fileInput.addEventListener("change", async () => {
    if (!fileInput.files || fileInput.files.length === 0) {
      hideStatus();
      return;
    }

    const file = fileInput.files[0];
    if (file.type !== "application/pdf") {
      showStatus("Only PDF files are supported for recognition.", "danger");
      return;
    }

    const formData = new FormData();
    formData.append("invoiceFile", file);

    showStatus("Reading PDF and extracting fields…", "info");

    try {
      const response = await fetch("/api/ocr", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        const message =
          (result && result.message) ||
          "Failed to recognise the invoice. Please fill in the fields manually.";
        showStatus(message, "danger");
        return;
      }

      const data = result.data || {};

      Object.entries(fieldMap).forEach(([key, input]) => {
        if (!input) {
          return;
        }
        const value = data[key];
        if (value === null || value === undefined || value === "") {
          return;
        }

        // Special handling for different field types
        if (key === "total_amount") {
          input.value = typeof value === "number" ? value.toFixed(2) : value;
        } else if (key === "invoice_date" && flatpickrInstances[input.id]) {
          // Use Flatpickr API to set date value
          flatpickrInstances[input.id].setDate(value, true);
        } else {
          input.value = value;
        }
      });

      const warnings = Array.isArray(result.warnings) ? result.warnings : [];
      if (warnings.length > 0) {
        showStatus(
          `Some details were not detected automatically: ${warnings.join(" ")}`,
          "warning"
        );
      } else {
        showStatus("Invoice details populated. Please review before saving.", "success");
      }
    } catch (error) {
      showStatus("Unexpected error while reading the PDF. Please try again.", "danger");
      console.error(error);
    }
  });
});
