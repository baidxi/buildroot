#include <stdio.h>
#include <errno.h>

#include "keymap.h"


const char *keyname_idx[GUI_KEYCODE_MAX] = {
       [POWER_BUTTON] = "POWER_BUTTON",
       [SOUTH_BUTTON] = "SOUTH_BUTTON",
       [EAST_BUTTON] = "EAST_BUTTON",
       [VOLUME_DOWN_BUTTON] = "VOLUME_DOWN_BUTTON",
       [NORTH_BUTTON] = "NORTH_BUTTON",
       [WEST_BUTTON] = "WEST_BUTTON",
       [VOLUME_UP_BUTTON] = "VOLUME_UP_BUTTON",
       [LEFT_BUMPER_BUTTON] = "LEFT_BUMPER_BUTTON",
       [RIGHT_BUMPER_BUTTON] = "RIGHT_BUMPER_BUTTON",
       [SELECT_BUTTON] = "SELECT_BUTTON",
       [START_BUTTON] = "START_BUTTON",
       [MODE_BUTTON] = "MODE_BUTTON",
       [LEFT_THUMB_BUTTON] = "LEFT_THUMB_BUTTON",
       [RIGHT_THUMB_BUTTON] = "RIGHT_THUMB_BUTTON",
};

int joykeyname2code(const char *name)
{
    for (int i = 0; i < GUI_KEYCODE_MAX; i++) {
        if (strcmp(name, keyname_idx[i]) == 0)
            return i;
    }

    return -1;
}

int kbname2code(const char *name)
{
    return -1;
}

typedef int (*func_t)(const char *name);

int keymap_parse_from_file(struct gui_context_inputs *input, const char *file)
{
    char buf[1024];
    short *map;
    fprintf(stdout, "open %s\n", file);
    FILE *fp = fopen(file, "r");
    func_t keyname2code;

    if (!fp) {
        perror("fopen");
        return -errno;
    }


    fprintf(stdout, "keymap.txt load OK\n");

    while(fgets(buf, sizeof(buf), fp)) {
        char *tok;
        char *key;
        char *code;
        int num_code;
        int num_key;

        if (buf[0] == '[') {
            buf[strlen(buf)] = '\0';
            buf[strlen(buf)-2] = '\0';
            char *name = buf+1;
            if (strcmp(name, "JOYSTICK") == 0) {
                map = input->joy_keymap;
                keyname2code = joykeyname2code;
            } else if (strcmp(name, "KEYBOARD") == 0) {
                map = input->kb_keymap;
                keyname2code = kbname2code;
            } else {
                continue;
            }
            continue;
        }

        tok = strtok(buf, "=");
        key = tok;
        code = strtok(NULL, "=");

        if (!key || !code)
            continue;

        num_code = strtol(code, NULL, 0);

        if (num_code > SDLK_LAST)
            continue;

        num_key = keyname2code(key);

        // printf("key %s map to %d, %d\n", key, num_key, num_code);

        if (num_code >= 0)
            map[num_code] = num_key;

        printf("%s map to %d\n", key, num_code);
    }


    return 0;
}