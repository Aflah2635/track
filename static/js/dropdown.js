class CustomDropdown {
    constructor(container) {
        this.container = container;
        this.trigger = container.querySelector('.dropdown-trigger');
        this.menu = container.querySelector('.dropdown-menu');
        this.input = container.querySelector('input[type="hidden"]');
        this.valueDisplay = container.querySelector('.selected-text');
        this.options = container.querySelectorAll('.dropdown-item');
        this.isOpen = false;

        this.init();
    }

    init() {
        this.trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });

        this.trigger.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggle();
            } else if (e.key === 'Escape') {
                this.close();
            }
        });

        this.options.forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                this.select(option);
            });
        });

        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.close();
            }
        });
        
        // Handle pre-selected value
        if (this.input && this.input.value) {
            const selectedOption = Array.from(this.options).find(opt => opt.dataset.value === this.input.value);
            if (selectedOption) {
                this.updateUI(selectedOption);
            }
        }
    }

    toggle() {
        this.isOpen = !this.isOpen;
        this.container.classList.toggle('active', this.isOpen);
        this.trigger.setAttribute('aria-expanded', this.isOpen);
        
        if (this.isOpen) {
             // adjust position if needed? (simple absolute is usually fine)
        }
    }

    close() {
        this.isOpen = false;
        this.container.classList.remove('active');
        this.trigger.setAttribute('aria-expanded', 'false');
    }

    select(option) {
        const value = option.dataset.value;
        const text = option.querySelector('.item-name') ? option.querySelector('.item-name').textContent : option.textContent.trim();
        
        // Update hidden input
        if (this.input) {
            this.input.value = value;
            // Dispatch change event for dependencies (like category filtering)
            this.input.dispatchEvent(new Event('change', { bubbles: true }));
        }

        // Update UI
        this.updateUI(option);
        
        // Close
        this.close();

        // If this dropdown is submitted on change (like filters)
        if (this.container.dataset.submitOnChange === 'true') {
            this.container.closest('form').submit();
        }
        
        /* If specific callback needed, we can dispatch a custom event too */
        this.container.dispatchEvent(new CustomEvent('dropdown-change', { detail: { value, text } }));
    }

    updateUI(selectedOption) {
        // Remove active class from all
        this.options.forEach(opt => opt.classList.remove('active'));
        // Add to selected
        selectedOption.classList.add('active');
        
        // Update trigger text
        if (this.valueDisplay) {
            const nameEl = selectedOption.querySelector('.item-name');
            this.valueDisplay.textContent = nameEl ? nameEl.textContent : selectedOption.textContent.trim();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.custom-form-dropdown').forEach(el => {
        new CustomDropdown(el);
    });
});
