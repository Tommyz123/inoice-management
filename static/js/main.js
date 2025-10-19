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
        if (key === "total_amount") {
          input.value = typeof value === "number" ? value.toFixed(2) : value;
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
