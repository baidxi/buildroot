#include "gui.h"
#include "gui_menu.h"
#include "gui_network_menu.h"


void gui_activate_network_menu(struct gui_node *this)
{
    struct gui_network_menu_node_data *network_node_data = this->data;

    gui_activate_menu(this, gettext("Network Setup"));

    this->context->menu.active = this;
}
void gui_deactivate_network_menu(struct gui_node *this)
{
    if (this->context->menu.active == this) {

        gui_destroy_node(this, 0);
        gui_deactivate_menu(this);

        if (this->parent) {
            this->context->menu.active = this->parent;
        }
    }
}
void gui_update_network_menu(struct gui_node *this)
{
	// The south-facing face button was pressed
	if (this->context->inputs.internal.previous.south != this->context->inputs.internal.current.south && this->context->inputs.internal.current.south)
	{
		// Deactivate the current node
		this->deactivate(this);
	}
}
void gui_invalidate_network_menu(struct gui_node *this)
{

}