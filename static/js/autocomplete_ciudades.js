const ciudadesColombia = [
    "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena", "Cúcuta", "Ibagué", 
    "Bucaramanga", "Villavicencio", "Santa Marta", "Valledupar", "Pereira", "Montería", 
    "Pasto", "Manizales", "Neiva", "Armenia", "Sincelejo", "Riohacha", "Tunja", 
    "Quibdó", "Florencia", "Yopal", "Popayán", "Mocoa", "San Andrés", "Envigado",
    "Itagüí", "Soledad", "Bello", "Soacha", "Buenaventura", "Palmira"
];

function inicializarAutocompletado() {
    const inputsCiudad = document.querySelectorAll('input[name="ciudad"]');

    inputsCiudad.forEach(input => {
        // Crear contenedor de sugerencias
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'autocomplete-suggestions';
        
        // Estilo rápido inline para asegurar funcionalidad inmediata
        Object.assign(suggestionsContainer.style, {
            position: 'absolute',
            top: '100%',
            left: '0',
            right: '0',
            zIndex: '9999',
            background: 'white',
            borderRadius: '12px',
            marginTop: '5px',
            boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
            border: '1.5px solid #E0E0E0',
            display: 'none',
            overflow: 'hidden'
        });

        input.parentNode.style.position = 'relative';
        input.parentNode.appendChild(suggestionsContainer);

        input.addEventListener('input', function() {
            const val = this.value.trim().toLowerCase();
            suggestionsContainer.innerHTML = '';
            
            if (val.length < 1) {
                suggestionsContainer.style.display = 'none';
                return false;
            }

            const matches = ciudadesColombia.filter(c => 
                c.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").includes(val.normalize("NFD").replace(/[\u0300-\u036f]/g, ""))
                || c.toLowerCase().includes(val)
            ).slice(0, 6);

            if (matches.length > 0) {
                suggestionsContainer.style.display = 'block';
                matches.forEach(match => {
                    const div = document.createElement('div');
                    div.style.padding = '12px 16px';
                    div.style.cursor = 'pointer';
                    div.style.fontSize = '14px';
                    div.style.transition = 'background 0.2s';
                    div.style.borderBottom = '1px solid #F0F0F0';
                    div.innerHTML = match;

                    div.onmouseover = () => div.style.background = '#FDF2F2';
                    div.onmouseout = () => div.style.background = 'white';

                    div.addEventListener('click', function() {
                        input.value = match;
                        suggestionsContainer.style.display = 'none';
                    });
                    suggestionsContainer.appendChild(div);
                });
            } else {
                suggestionsContainer.style.display = 'none';
            }
        });

        document.addEventListener('click', (e) => {
            if (!input.contains(e.target) && !suggestionsContainer.contains(e.target)) {
                suggestionsContainer.style.display = 'none';
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', inicializarAutocompletado);
