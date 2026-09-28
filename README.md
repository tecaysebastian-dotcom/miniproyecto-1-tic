# MiniProyecto 1: Taller de Aplicación TIC I (549253-1)
**Universidad de Concepción — Facultad de Ingeniería — Departamento de Ingeniería Eléctrica**  
*Carrera: Ingeniería Civil en Telecomunicaciones*

* **Profesor:** Vincenzo Caro
* **Ayudantes:** Joaquín Mardones / Álvaro Sagredo
* **Integrantes:**
  * Sebastián Tecay
  * Mahori Araki
  * Cristóbal Ferreira

---

## 📄 Documentación y Entregables
* **Informe Técnico Completo (PDF):** [Descargar Informe](./Informe_MiniProyecto1.pdf)
* **Demostraciones:**
  * 🎥 **Actividad 1 (Zona Safari Pokémon):** [Ver Video Demostrativo](https://youtu.be/XWqipDaZR9I)
  * 📖 **Actividad 2 (Consola Retro Recalbox):** Demostración y validación documentada mediante tutorial técnico detallado paso a paso dentro del informe.

---

## 🌿 Actividad 1: Zona Safari Pokémon en Raspberry Pi
Simulador interactivo por consola en Python (`tic1.py`) con control ambiental y periféricos físicos:
* **Sensor DHT11 (GPIO 12):** Lectura periódica de temperatura y humedad para habilitar hábitats dinámicos.
* **Conversor ADC ADS1115 (I2C):** Digitalización del eje vertical (VRy) del joystick analógico KY-023 para la navegación por menús.
* **Pulsador SW (GPIO 5):** Botón de confirmación y selección.
* **Buzzer Pasivo KY-006 (GPIO 6):** Frecuencias sonoras diferenciadas (400 Hz al mover, 800 Hz al seleccionar).
* **LEDs RGB 1 y 2:** Indicador de disponibilidad de fauna en el bioma y retroalimentación de capturas, huidas y efectividad de ataques.

---

## 🕹️ Actividad 2: Consola de Juegos Retro (Raspberry Pi 5)
Implementación de un centro de retroemulación independiente:
* **Hardware:** Raspberry Pi 5 (4 GB RAM) con microSD Kingston Canvas Select Plus de 32 GB Class 10.
* **Sistema Operativo:** Recalbox OS para Raspberry Pi 5 flasheado mediante *Raspberry Pi Imager*.
* **Emuladores y Sistemas:** SNES (*Snes9x*), Game Boy Advance (*mGBA*) y Sega Genesis (*Genesis Plus GX*).
* **Características:** Mapeo de Gamepad USB con tecla modificadora `Hotkey` (Select), guardado rápido de estados (*Save States*), raspado de metadatos y carátulas con *ScreenScraper*, y gestión por red local Samba.