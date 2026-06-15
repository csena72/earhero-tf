// app.js

document.addEventListener('DOMContentLoaded', () => {
  const apiUrl = 'https://api.earheroai.com/notes'; // Reemplaza con la URL correcta de tu API
  const cardsContainer = document.getElementById('cards-container');

  async function fetchNotes() {
    try {
      const response = await fetch(apiUrl);
      if (!response.ok) throw new Error(`Error fetching notes: ${response.statusText}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching notes:', error);
    }
  }

  function renderNotes(notes) {
    cardsContainer.innerHTML = '';
    notes.forEach(note => {
      const card = document.createElement('div');
      card.className = 'card';
      card.style.backgroundColor = '--violeta'; // Cambia el color de fondo al estilo del proyecto
      card.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
      card.style.borderRadius = '16px';

      const noteText = document.createElement('p');
      noteText.textContent = note.name; // Asegúrate de que la propiedad del nombre coincida con los datos
      noteText.style.color = '--texto';
      noteText.style.fontSize = '24px';
      noteText.style.textAlign = 'center';

      const playButton = document.createElement('button');
      playButton.className = 'play-button';
      playButton.textContent = '▶ Reproducir';
      playButton.onclick = () => {
        reproduceNote(note.audioUrl);
      };

      card.appendChild(noteText);
      card.appendChild(playButton);
      cardsContainer.appendChild(card);
    });
  }

  async function reproduceNote(audioUrl) {
    try {
      const audioElement = new Audio(audioUrl);
      audioElement.play();
    } catch (error) {
      console.error('Error reproducing note:', error);
    }
  }

  fetchNotes().then(notes => {
    renderNotes(notes);
  });
});