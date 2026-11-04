// Toolchain smoke test: blinks the LED on GP25 (Pico and its clones). Not part of the product.
#include "pico/stdlib.h"

int main(void) {
    const uint led = PICO_DEFAULT_LED_PIN;
    gpio_init(led);
    gpio_set_dir(led, GPIO_OUT);
    for (;;) {
        gpio_put(led, 1);
        sleep_ms(250);
        gpio_put(led, 0);
        sleep_ms(250);
    }
}
