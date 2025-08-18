document.addEventListener('DOMContentLoaded', function() {
    // Step 1: Space Selection
    const spaceCards = document.querySelectorAll('.space-card');
    let selectedSpace = null;
    
    spaceCards.forEach(card => {
        card.addEventListener('click', function() {
            spaceCards.forEach(c => c.classList.remove('border-primary'));
            this.classList.add('border-primary');
            selectedSpace = {
                id: this.dataset.spaceId,
                name: this.querySelector('.card-title').textContent,
                price: parseFloat(this.querySelector('li:nth-child(2)').textContent.match(/\d+/)[0])
            };
        });
    });
    
    // Navigation between steps
    document.getElementById('nextToStep2').addEventListener('click', function() {
        if (!selectedSpace) {
            alert('Veuillez sélectionner un espace');
            return;
        }
        document.getElementById('step2-tab').removeAttribute('disabled');
        document.getElementById('step2-tab').click();
    });
    
    document.getElementById('backToStep1').addEventListener('click', function() {
        document.getElementById('step1-tab').click();
    });
    
    document.getElementById('nextToStep3').addEventListener('click', function() {
        const date = document.getElementById('bookingDate').value;
        const startTime = document.getElementById('startTime').value;
        const endTime = document.getElementById('endTime').value;
        
        if (!date || !startTime || !endTime) {
            alert('Veuillez remplir tous les champs');
            return;
        }
        
        // Update summary
        document.getElementById('summarySpace').textContent = `Espace: ${selectedSpace.name}`;
        document.getElementById('summaryDateTime').textContent = `Date: ${date} de ${startTime} à ${endTime}`;
        
        const duration = calculateDuration(startTime, endTime);
        document.getElementById('summaryDuration').textContent = `Durée: ${duration} heures`;
        
        const totalPrice = (duration * selectedSpace.price).toFixed(2);
        document.getElementById('summaryPrice').textContent = `Prix total: ${totalPrice}€`;
        
        document.getElementById('step3-tab').removeAttribute('disabled');
        document.getElementById('step3-tab').click();
    });
    
    document.getElementById('backToStep2').addEventListener('click', function() {
        document.getElementById('step2-tab').click();
    });
    
    // Time slot management
    document.getElementById('startTime').addEventListener('change', function() {
        const endTimeSelect = document.getElementById('endTime');
        endTimeSelect.innerHTML = '<option value="">Sélectionner</option>';
        
        if (this.value) {
            endTimeSelect.disabled = false;
            const startIndex = time_slots.indexOf(this.value);
            
            for (let i = startIndex + 1; i < time_slots.length; i++) {
                const option = document.createElement('option');
                option.value = time_slots[i];
                option.textContent = time_slots[i];
                endTimeSelect.appendChild(option);
            }
        } else {
            endTimeSelect.disabled = true;
        }
    });
    
    // Helper function to calculate duration
    function calculateDuration(start, end) {
        const startParts = start.split(':');
        const endParts = end.split(':');
        
        const startDate = new Date(0, 0, 0, startParts[0], startParts[1]);
        const endDate = new Date(0, 0, 0, endParts[0], endParts[1]);
        
        let diff = endDate.getTime() - startDate.getTime();
        return Math.round((diff / (1000 * 60 * 60)) || 1;
    }
    
    // Confirm booking
    document.getElementById('confirmBooking').addEventListener('click', function() {
        // Here you would typically send the data to your backend
        alert('Réservation confirmée! Un email de confirmation vous a été envoyé.');
        // Reset form
        document.getElementById('step1-tab').click();
        spaceCards.forEach(c => c.classList.remove('border-primary'));
        document.getElementById('bookingDate').value = '';
        document.getElementById('startTime').value = '';
        document.getElementById('endTime').value = '';
        document.getElementById('endTime').disabled = true;
        selectedSpace = null;
    });
});