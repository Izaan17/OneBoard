// Function to update the displayed URL
function updateSavedUrl() {
    fetch('/get_calendar_url')
        .then(response => response.json())
        .then(data => {
            const savedUrlElement = document.getElementById('savedUrl');
            savedUrlElement.innerText = data.calendar_url ? 'Current URL: ' + data.calendar_url : 'No calendar URL saved.';
        })
        .catch(error => {
            console.error('Error:', error);
        });
}
// Display the saved calendar URL on page load
updateSavedUrl();


document.getElementById('toggleFormButton').addEventListener('click', function () {
    var form = document.getElementById('addForm');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
});

document.getElementById('loadFromBBButton').addEventListener('click', function () {
            // Fetch calendar data
            fetch('/fetch_calendar')
                .then(response => response.text())
                .then(data => {
                    console.log('Calendar data fetched:', data);
                    location.reload(true);
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error fetching data.');
                });
        });

// Button to change the calendar URL
document.getElementById('changeUrlButton').addEventListener('click', function () {
            const newCalendarUrl = prompt('Enter the new calendar URL:');
            if (newCalendarUrl) {
                // Save the new calendar URL
                fetch('/save_calendar_url', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ calendar_url: newCalendarUrl }),
                })
                .then(response => response.json())
                .then(data => {
                    console.log(data.message);
                    // Update the displayed URL
                    updateSavedUrl();
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            } else {
                alert('No new calendar URL provided.');
            }
        });

// Add this function to handle mass deletion
function massDeleteAssignments() {
    if (confirm('Are you sure you want to delete all assignments?')) {
        fetch('/clear_all', {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            location.reload(true);

        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting assignments.');
        });
    }
}

// Button to mass delete all assignments
document.getElementById('massDeleteButton').addEventListener('click', function () {
    massDeleteAssignments();
});

// Function to update completion status
function updateCompletionStatus(assignmentId, isComplete) {
    fetch(`/complete/${assignmentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_complete: isComplete }),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
        if (data.is_complete !== undefined) {
            // Do something with the updated is_complete value if needed
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating completion status.');
    });
}


// Event listener for checkbox changes
document.addEventListener('change', function (event) {
    const target = event.target;
    if (target.type === 'checkbox' && target.id.startsWith('complete-')) {
        const assignmentId = target.id.split('-')[1];
        const isComplete = target.checked;
        updateCompletionStatus(assignmentId, isComplete);
    }
});