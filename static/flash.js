/*---------------------------------- Toggle profile  -------------------------*/

function toggleProfile() {
    var card = document.getElementById("profileCard");
    card.style.display = (card.style.display === "block") ? "none" : "block";
}

// ✅ dagdag na auto-close kapag click sa labas
document.addEventListener("click", function(e) {
    const profileCard = document.getElementById("profileCard");
    const profileIcon = document.querySelector(".profile-icon");

    if (profileCard.style.display === "block" &&
        !profileCard.contains(e.target) &&
        !profileIcon.contains(e.target)) {
        profileCard.style.display = "none";
    }
});

/*----------------------------- Organizer Type ----------------------------*/
document.addEventListener('DOMContentLoaded', function() {
    const roleSelect = document.getElementById('role');
    const organizerTypeDiv = document.getElementById('organizerType');

    roleSelect.addEventListener('change', function() {
        if (this.value === 'organizer') {
            organizerTypeDiv.style.display = 'block';
        } else {
            organizerTypeDiv.style.display = 'none';
        }
    });
});

/*----------------------------- notification ----------------------------*/


function toggleNotif() {
    const dropdown = document.getElementById("notifDropdown");
    dropdown.classList.toggle("show");
}

// Close dropdown if clicking outside
document.addEventListener("click", function(e) {
    const dropdown = document.getElementById("notifDropdown");
    const bell = document.getElementById("notifBell");
    if (!bell.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove("show");
    }
});







