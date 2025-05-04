#ifndef _GUI_NETWORK_MENU_H_
#define _GUI_NETWORK_MENU_H_

#include "gui.h"

void gui_activate_network_menu(struct gui_node *this);
void gui_deactivate_network_menu(struct gui_node *this);
void gui_update_network_menu(struct gui_node *this);
void gui_invalidate_network_menu(struct gui_node *this);

#endif