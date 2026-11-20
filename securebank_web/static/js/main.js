// SecureBank Frontend JavaScript

document.addEventListener("DOMContentLoaded", function () {
  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert:not(.alert-permanent)");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      try {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } catch (e) {
        alert.style.display = "none";
      }
    }, 5000);
  });

  // Copy Account Number button
  const copyBtn = document.getElementById("copyAccountBtn");
  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      const accNo = this.getAttribute("data-account");
      if (accNo) {
        navigator.clipboard.writeText(accNo).then(function () {
          const originalText = copyBtn.innerHTML;
          copyBtn.innerHTML = '<i class="bi bi-check-lg"></i> Copied!';
          copyBtn.classList.remove("btn-outline-secondary");
          copyBtn.classList.add("btn-success");

          setTimeout(function () {
            copyBtn.innerHTML = originalText;
            copyBtn.classList.remove("btn-success");
            copyBtn.classList.add("btn-outline-secondary");
          }, 2000);
        }).catch(function (err) {
          console.error("Failed to copy account number:", err);
        });
      }
    });
  }

  // Toggle Password Visibility
  const togglePassBtns = document.querySelectorAll(".toggle-password-btn");
  togglePassBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      const targetId = this.getAttribute("data-target");
      const targetInput = document.getElementById(targetId);
      if (targetInput) {
        const isPassword = targetInput.getAttribute("type") === "password";
        targetInput.setAttribute("type", isPassword ? "text" : "password");
        const icon = this.querySelector("i");
        if (icon) {
          icon.classList.toggle("bi-eye", !isPassword);
          icon.classList.toggle("bi-eye-slash", isPassword);
        }
      }
    });
  });

  // Transfer form confirmation modal or prompt
  const transferForm = document.getElementById("transferForm");
  if (transferForm) {
    transferForm.addEventListener("submit", function (e) {
      const receiver = document.getElementById("receiver_account").value.trim();
      const amount = document.getElementById("amount").value.trim();
      if (receiver && amount) {
        const confirmed = confirm(`Are you sure you want to transfer ₹${amount} to Account #${receiver}?`);
        if (!confirmed) {
          e.preventDefault();
        }
      }
    });
  }
});
