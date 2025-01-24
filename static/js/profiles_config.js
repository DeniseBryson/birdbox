/**
 * Configuration Profiles Module
 * Handles loading and managing different system configuration profiles
 */

async function loadProfiles() {
    try {
        const response = await fetch('/api/v1/config/profiles');
        const data = await response.json();
        updateProfilesList(data.profiles);
    } catch (error) {
        console.error('Error loading profiles:', error);
    }
}

function updateProfilesList(profiles) {
    const list = document.getElementById('profiles-list');
    if (!list) return;
    
    // Keep default profile
    const defaultProfile = list.querySelector('[data-profile="default"]');
    list.innerHTML = '';
    if (defaultProfile) list.appendChild(defaultProfile);
    
    // Add other profiles
    profiles.forEach(profile => {
        if (profile.name === 'default') return;
        const item = document.createElement('a');
        item.href = '#';
        item.className = 'list-group-item list-group-item-action';
        item.setAttribute('data-profile', profile.name);
        item.textContent = profile.name;
        list.appendChild(item);
    });
}

async function loadProfileSettings(profileName) {
    try {
        const response = await fetch(`/api/v1/config/profiles/${profileName}`);
        const data = await response.json();
        
        // Update form values
        document.getElementById('motor-frequency').value = data.motor_frequency || 50;
        document.getElementById('sensor-sensitivity').value = data.sensor_sensitivity * 100 || 75;
        document.getElementById('feeding-delay').value = data.feeding_delay || 5;
    } catch (error) {
        console.error('Error loading profile settings:', error);
    }
}

async function saveProfile(event) {
    event.preventDefault();
    const activeProfile = document.querySelector('#profiles-list .active').getAttribute('data-profile');
    
    try {
        const data = {
            name: activeProfile,
            motor_frequency: parseInt(document.getElementById('motor-frequency').value),
            sensor_sensitivity: parseFloat(document.getElementById('sensor-sensitivity').value) / 100,
            feeding_delay: parseInt(document.getElementById('feeding-delay').value)
        };
        
        const response = await fetch(`/api/v1/config/profiles/${activeProfile}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert('Profile saved successfully');
        } else {
            alert('Failed to save profile');
        }
    } catch (error) {
        console.error('Error saving profile:', error);
        alert('Error saving profile');
    }
}

// Initialize profiles UI
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('profile-config-form');
    const profilesList = document.getElementById('profiles-list');
    const addButton = document.getElementById('add-profile');
    const deleteButton = document.getElementById('delete-profile');
    
    if (form) form.addEventListener('submit', saveProfile);
    if (profilesList) {
        profilesList.addEventListener('click', (e) => {
            if (e.target.hasAttribute('data-profile')) {
                e.preventDefault();
                // Update active state
                profilesList.querySelectorAll('a').forEach(a => a.classList.remove('active'));
                e.target.classList.add('active');
                // Load profile settings
                loadProfileSettings(e.target.getAttribute('data-profile'));
            }
        });
    }
    
    // Load initial profiles
    loadProfiles();
}); 