'use strict';

let editor;
let editor_is_ready = false;
let currentProfileEditAction = '';
let fetchingTerminalOutput = false;
let pendingClearTerminalOutput = false;

const pageRefreshDelay = 400;
const statusIconDisappearDelay = 400;
const terminalOutputDisplayRefreshDelay = 200;

const pathName = window.location.pathname;
const pathNameParts = pathName.split('/').filter(part => part !== '');
const profileName = pathNameParts[pathNameParts.length - 1];
const configName = pathNameParts[pathNameParts.length - 2];

const navbarMenu = document.querySelector("#navbar-menu");
const configSelect = document.querySelector('#config-select');

const saveActionButtons = document.querySelectorAll('.save-action');
const resetActionButtons = document.querySelectorAll('.reset-action');
const launchActionButtons = document.querySelectorAll('.launch-action');
const terminateActionButtons = document.querySelectorAll('.terminate-action');

const flashMessagesContent = document.querySelector('#flash-messages-content');

const profileContainer = document.querySelector('#profile-container');

const profileNameEditTexts = document.querySelectorAll(".profile-name-edit")

const profileConfirmGroups = document.querySelectorAll('.profile-confirm-group');
const profileConfirmButtons = document.querySelectorAll('.profile-confirm');
const profileCancelButtons = document.querySelectorAll('.profile-cancel');

const profileActionsGroups = document.querySelectorAll('.profile-actions-group');
const profileAddButtons = document.querySelectorAll('.profile-add');
const profileRenameButtons = document.querySelectorAll('.profile-rename');
const profileDeleteButtons = document.querySelectorAll('.profile-delete');

const profileSelect = document.querySelector('#profile-select');

const configFormLoadingIcon = document.querySelector('#config-form-loading-icon');
const configFormLoadingIconBaseClassName = configFormLoadingIcon.className;
const configFormContent = document.querySelector('#config-form-content');
const configFormEdit = document.querySelector('#config-form-edit');
const configFormContentPlaceholder = document.querySelector('#config-form-content-placeholder');

const jsonCodeExpandButton = document.querySelector('#json-code-expand');
const jsonCodeCollapseButton = document.querySelector('#json-code-collapse');
const jsonCodeContent = document.querySelector('#json-code-content');
const jsonCodeEdit = document.querySelector('#json-code-edit');
const jsonCodeContentPlaceholder = document.querySelector('#json-code-content-placeholder');
const jsonCodeContentPlaceholderLabel = jsonCodeContentPlaceholder.querySelector('button > span');

const terminalOutputHeading = document.querySelector('#terminal-output-heading');
const mainProgramRunningIcon = document.querySelector('#main-program-running-icon');
const mainProgramRunningIconBaseClassName = mainProgramRunningIcon.className;
const terminalOutputRefreshButton = document.querySelector('#terminal-output-refresh');
const terminalOutputClearButton = document.querySelector('#terminal-output-clear');
const terminalOutputDisplay = document.querySelector('#terminal-output-display');
const terminalOutputDisplayBaseClassName = terminalOutputDisplay.className;

const bsCollapseNavbarMenu = new bootstrap.Collapse(navbarMenu, { toggle: false });
const bsCollapseConfigFormContent = new bootstrap.Collapse(configFormContent, { toggle: false });
const bsCollapseConfigFormContentPlaceHolder = new bootstrap.Collapse(configFormContentPlaceholder, { toggle: false });
const bsCollapsejsonCodeContent = new bootstrap.Collapse(jsonCodeContent, { toggle: false });
const bsCollapsejsonCodeContentPlaceholder = new bootstrap.Collapse(jsonCodeContentPlaceholder, { toggle: false });

function focusElementFromHash() {
    const hash = window.location.hash;
    if (hash) {
        const target = document.querySelector(hash);
        if (target) {
            target.focus();
        }
    }
}

function collapseNavbar() {
    bsCollapseNavbarMenu.hide();
}

function navigateToConfig() {
    const selectedValue = configSelect.value;
    if (selectedValue) {
        window.location.href = selectedValue;
    } else {
        window.location.href = '/';
    }
}

function flashMessage(message, category, scroll = true) {
    const iconClass = {
        'info': 'fas fa-info-circle',
        'success': 'fas fa-check-circle',
        'warning': 'fas fa-exclamation-triangle',
        'danger': 'fas fa-times-circle'
    };
    const messageHTML = `
        <div class="alert alert-${category} alert-dismissible fade show" role="alert">
            <div>
                <span><i class="${iconClass[category]}"></i></span>
                <span>${message}</span>
            </div>
            <button class="btn-close" type="button" title="Dismiss" data-bs-dismiss="alert" aria-label="Dismiss"></button>
        </div>
    `;
    flashMessagesContent.insertAdjacentHTML('beforeend', messageHTML);
    if (scroll) {
        window.scroll({
            top: 0,
            behavior: 'smooth'
        });
    }
    return messageHTML;
}

function clearFlashMessage() {
    flashMessagesContent.innerHTML = '';
}

function navigateToProfile() {
    const selectedValue = profileSelect.value;
    if (selectedValue) {
        window.location.href = selectedValue;
    } else {
        window.location.href = '/';
    }
}

async function manageProfiles(action, profileNameEditText) {
    if (action === 'confirm') {
        if (!profileNameEditText) {
            return;
        }
        let res;
        if (currentProfileEditAction === 'add') {
            res = await updateProfile('add', profileNameEditText.value);
            if (res) setTimeout(() => { window.location.href = `/config/${configName}/${profileNameEditText.value}`; }, pageRefreshDelay);
        } else if (currentProfileEditAction === 'rename') {
            res = await updateProfile('rename', profileNameEditText.value);
            if (res) setTimeout(() => { window.location.href = `/config/${configName}/${profileNameEditText.value}`; }, pageRefreshDelay);
        } else if (currentProfileEditAction === 'delete') {
            res = await updateProfile('delete', profileName);
            if (res) setTimeout(() => { window.location.href = `/config/${configName}`; }, pageRefreshDelay);
        }
        manageProfiles('cancel', null);
    } else if (action === 'cancel') {
        currentProfileEditAction = '';
        editor.enable();
        profileNameEditTexts.forEach(element => { element.style.display = 'none'; });
        profileConfirmGroups.forEach(element => { element.style.display = 'none'; });
        profileActionsGroups.forEach(element => { element.style.removeProperty('display'); });
    } else {
        currentProfileEditAction = action;
        editor.disable();
        if (action !== 'delete') {
            profileNameEditTexts.forEach(element => { element.style.removeProperty('display'); });
            profileCancelButtons.forEach(element => { element.className = 'btn btn-danger'; });
            if (action === 'add') {
                profileNameEditTexts.forEach(element => { element.value = ''; });
                profileConfirmButtons.forEach(element => { element.className = 'btn btn-success'; });
            } else if (action === 'rename') {
                profileNameEditTexts.forEach(element => { element.value = decodeURIComponent(profileName); });
                profileConfirmButtons.forEach(element => { element.className = 'btn btn-primary'; });
            }
        } else {
            profileNameEditTexts.forEach(element => { element.style.display = 'none'; });
            profileConfirmButtons.forEach(element => { element.className = 'btn btn-danger'; });
            profileCancelButtons.forEach(element => { element.className = 'btn btn-primary'; });
        }
        profileConfirmGroups.forEach(element => { element.style.removeProperty('display'); });
        profileActionsGroups.forEach(element => { element.style.display = 'none'; });
    }
}
async function getConfigAndSchema() {
    let res = {};
    try {
        const response = await fetch('/api' + pathName, { method: 'GET' });
        const data = await response.json();
        res.config = data.config;
        res.schema = data.schema;
        if (data.success) {
            configFormLoadingIcon.className = configFormLoadingIconBaseClassName + ' text-success';
        }
        else {
            configFormLoadingIcon.className = configFormLoadingIconBaseClassName + ' text-danger';
            flashMessage('Failed to get config from server.', 'danger');
        }
    }
    catch (error) {
        flashMessage('Failed to get config from server.', 'danger');
        configFormLoadingIcon.className = configFormLoadingIconBaseClassName + ' text-danger';
    }
    return res;
}

function hasPasswordFormat(schema) {
    if (typeof schema !== "object" || schema === null) {
        return false;
    }

    if (schema.format === "password") {
        return true;
    }

    if (schema.properties) {
        for (const key in schema.properties) {
            if (hasPasswordFormat(schema.properties[key])) {
                return true;
            }
        }
    }

    if (schema.items) {
        if (Array.isArray(schema.items)) {
            for (const item of schema.items) {
                if (hasPasswordFormat(item)) {
                    return true;
                }
            }
        } else if (hasPasswordFormat(schema.items)) {
            return true;
        }
    }

    if (schema.anyOf || schema.oneOf || schema.allOf) {
        const schemas = schema.anyOf || schema.oneOf || schema.allOf;
        for (const subSchema of schemas) {
            if (hasPasswordFormat(subSchema)) {
                return true;
            }
        }
    }

    return false;
}

function changeCheckboxStyle() {
    const checkboxes = configFormEdit.querySelectorAll('input[type="checkbox"]');

    checkboxes.forEach(input => {
        if (input.parentElement.tagName.toLowerCase() === 'span' && input.parentElement.attributes.length === 0) {
            // Get it out of span
            const parentSpan = input.parentElement;
            const parentOfParent = parentSpan.parentElement;
            while (parentSpan.firstChild) {
                parentOfParent.insertBefore(parentSpan.firstChild, parentSpan);
            }
            parentSpan.remove();
        }

        const parent = input.parentElement;
        const newLabel = document.createElement('label');
        newLabel.setAttribute('for', input.id);

        parent.removeAttribute('for');
        if (parent.classList.contains('editor-check') || parent.classList.contains('check-list')) {
            return;
        }

        input.className += ' form-check-input editor-check-input';
        if (parent.tagName.toLowerCase() === 'label') {
            input.className += ' form-check-input editor-check-input check-input-plain';
            parent.className = 'form-check editor-check';
            newLabel.className = 'form-check-label check-label-plain';
            parent.insertBefore(newLabel, input.nextSibling);
        } else if (parent.tagName.toLowerCase() === 'span') {
            input.className += ' form-check-input editor-check-input check-input-heading';
            parent.className = 'form-check editor-check d-inline-flex';
            newLabel.className = 'form-check-label check-label-heading';

            parent.childNodes.forEach(child => {
                if (child.nodeType === Node.TEXT_NODE && child.textContent.trim() !== '') {
                    newLabel.appendChild(child);
                }
            });
            parent.insertBefore(newLabel, input.nextSibling);
        } else if (parent.tagName.toLowerCase() === 'b') {
            input.className += ' form-check-input editor-check-input check-input-plain';
            parent.className = 'form-check editor-check user-add-item';
            newLabel.className = 'form-check-label check-label-plain';

            parent.insertBefore(newLabel, input.nextSibling);

            const newParent = document.createElement('label');
            while (parent.firstChild) {
                newParent.appendChild(parent.firstChild);
            }
            Array.from(parent.attributes).forEach(attr => {
                newParent.setAttribute(attr.name, attr.value);
            });
            parent.replaceWith(newParent);
        } else if (parent.tagName.toLowerCase() === 'div') {
            console.log(parent)
            parent.className += ' check-list'
            const formLabelElement = parent.querySelector('label[class="form-check-label"]')
            formLabelElement.textContent = formLabelElement.textContent.trim()

            const newParent = document.createElement('label');
            while (parent.firstChild) {
                newParent.appendChild(parent.firstChild);
            }
            Array.from(parent.attributes).forEach(attr => {
                newParent.setAttribute(attr.name, attr.value);
            });
            parent.replaceWith(newParent);
        }
    });
}
function changeButtonGroupStyle() {
    const buttonGroups = document.querySelectorAll('span.btn-group');
    buttonGroups.forEach(buttonGroup => {
        if (buttonGroup.style.display === 'inline-block') {
            buttonGroup.removeAttribute('style');
        }
        if (buttonGroup.querySelector('button.json-editor-btntype-delete') !== null) {
            buttonGroup.classList.add('mb-1');
        }
    });
}

function setAnchor() {
    document.querySelectorAll('[data-schemapath]').forEach(element => {
        if (!element.id) {
            const dataSchemaPath = element.getAttribute('data-schemapath')
            // root.a.b.c => root[a][b][c]
            const parts = dataSchemaPath.split('.');
            const anchor = parts.map((part, index) => {
                return index >= 1 ? `[${part}]` : part;
            }).join('');
            if (!document.getElementById(anchor)) {
                element.id = anchor;
            }
        }
    });
}

function changeStyle() {
    changeCheckboxStyle();
    changeButtonGroupStyle();
    setAnchor();
}

function showConfigFormContent() {
    setTimeout(() => { bsCollapseConfigFormContent.show(); }, 0);
    setTimeout(() => { bsCollapseConfigFormContentPlaceHolder.hide(); }, 0);
}

function toggleJsonCodeContent(action) {
    if (action === 'show') {
        setTimeout(() => { bsCollapsejsonCodeContent.show(); }, 0);
        setTimeout(() => { bsCollapsejsonCodeContentPlaceholder.hide(); }, 0);
        jsonCodeExpandButton.style.display = 'none';
        jsonCodeCollapseButton.style.removeProperty('display');
    } else if (action === 'hide') {
        setTimeout(() => { bsCollapsejsonCodeContent.hide(); }, 0);
        setTimeout(() => { bsCollapsejsonCodeContentPlaceholder.show(); }, 0);
        jsonCodeExpandButton.style.removeProperty('display');
        jsonCodeCollapseButton.style.display = 'none';
    } else {
        return;
    }
}

async function updateProfile(action, profileName) {
    clearFlashMessage();
    let method;
    let requestData = {};
    requestData.name = decodeURIComponent(profileName);
    if (action === 'update') {
        const errors = editor.validate();

        if (errors.length) {
            errors.forEach(error => {
                // root.a.b.c => root[a][b][c]
                const parts = error.path.split('.');
                const href = parts.map((part, index) => {
                    return index >= 1 ? `[${part}]` : part;
                }).join('');

                flashMessage(`Property "<b>${error.property}</b>" unsatisfied at {<a href="#${href}" class="alert-link">${error.path}</a>}: ${error.message}`, 'danger');
            });
            return;
        }
        method = 'PATCH';
        const configValue = editor.getValue();
        requestData.config = configValue;
    } else if (action === 'add') {
        method = 'POST';
    } else if (action === 'rename') {
        method = 'PUT';
    } else if (action === 'delete') {
        method = 'DELETE';
    } else {
        return;
    }

    try {
        const response = await fetch(`/api${pathName}`, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        const data = await response.json();
        let messageCategory;
        if (data.success) {
            messageCategory = 'success';
        } else {
            messageCategory = 'danger';
        }
        for (const message of data.messages) {
            flashMessage(message, messageCategory);
        }
        return data.success;
    } catch (error) {
        flashMessage('Failed to update profile. Is the backend service working properly?', 'danger');
        return false;
    }
}

async function reload() {
    clearFlashMessage();
    const configAndSchema = await getConfigAndSchema();
    editor.setValue(configAndSchema.config);
    setTimeout(() => changeStyle(), 0);
}

async function launch() {
    clearFlashMessage();
    try {
        const response = await fetch(`/api/launch`, {
            method: 'GET',
        });
        const data = await response.json();
        const messageCategory = (data.success ? 'success' : 'danger');
        const scroll = (data.success ? false : true);
        for (const message of data.messages) {
            flashMessage(message, messageCategory, scroll);
        }
        if (!scroll) {
            terminalOutputHeading.scrollIntoView({ behavior: "smooth" });
            terminalOutputDisplay.focus();
        }
        return data.success;
    } catch (error) {
        flashMessage('Failed to launch the main program. Checkout your python backend.', 'danger');
        return false;
    }
}

async function terminate() {
    clearFlashMessage();
    try {
        flashMessage('Trying to terminate the editor backend. Subsequent changes will not be saved.', 'warning');
        await fetch(`/api/shutdown`, {
            method: 'GET',
        });
    } catch (error) {
        flashMessage('Failed to terminate the editor backend. Maybe it is already terminated.', 'danger');
    }
}

async function initializeConfigFormEditor() {
    configFormLoadingIcon.className = configFormLoadingIconBaseClassName + ' text-primary';
    configFormLoadingIcon.style.display = 'inline-block';
    const configAndSchema = await getConfigAndSchema();
    const myschema = configAndSchema.schema;
    const myconfig = configAndSchema.config;
    const jsonEditorConfig = {
        form_name_root: configName,
        iconlib: 'fontawesome5',
        theme: 'bootstrap5',
        show_opt_in: true,
        disable_edit_json: true,
        disable_properties: true,
        disable_collapse: false,
        enable_array_copy: true,
        no_additional_properties: true,
        enforce_const: true,
        startval: myconfig,
        schema: myschema
    };
    editor = new JSONEditor(configFormEdit, jsonEditorConfig);
    editor.on('change', function () {
        if (editor_is_ready) {
            setTimeout(() => changeStyle(), 0);
            jsonCodeEdit.value = JSON.stringify(editor.getValue(), null, 4);
        }
    });
    editor.on('ready', function () {
        editor_is_ready = true;
        setTimeout(() => { changeStyle(); }, 0);
        showConfigFormContent();
        if (hasPasswordFormat(myschema)) {
            jsonCodeContentPlaceholderLabel.textContent = 'Expanding JSON may expose sensitive information.';
            jsonCodeExpandButton.className = 'btn btn-outline-danger';
        } else {
            toggleJsonCodeContent('show');
        }
        setTimeout(() => { configFormLoadingIcon.style.display = 'none'; }, statusIconDisappearDelay)
        jsonCodeEdit.wrap = "off";
    });
}

function processCarriageReturn(input) {
    const lines = input.split('\n');

    const processedLines = lines.map(line => {
        const parts = line.split('\r');
        let result = '';

        for (let i = parts.length - 1; i >= 0; i--) {
            result = result + parts[i].substring(result.length);
        }

        return result;
    });

    return processedLines.join('\n');
}

async function clearTerminalOutput() {
    const url = "/api/clear_terminal_output";
    await fetch(url, {
        method: 'POST',
    });
    pendingClearTerminalOutput = true;
    terminalOutputDisplay.value = '';
    terminalOutputDisplay.wrap = "on";
    terminalOutputDisplay.className = terminalOutputDisplayBaseClassName;
}

function getTerminalOutput(recentOnly) {
    if (fetchingTerminalOutput) {
        return;
    }
    let lastRequestComplete = true;
    const url = "/api/get_terminal_output";
    const err_message = 'Failed to get output from the main program.';
    if (!recentOnly) {
        console.log('yes')
        terminalOutputDisplay.value = '';
    }
    let textSinceLastLine = '';
    let textUntilLastLine = terminalOutputDisplay.value;
    terminalOutputDisplay.className = terminalOutputDisplayBaseClassName;
    terminalOutputDisplay.scrollTop = terminalOutputDisplay.scrollHeight;

    mainProgramRunningIcon.className = mainProgramRunningIconBaseClassName + ' text-primary';

    const intervalId = setInterval(async () => {
        if (!lastRequestComplete) {
            return;
        }
        mainProgramRunningIcon.style.display = 'inline-block';
        try {
            lastRequestComplete = false;
            if (pendingClearTerminalOutput) {
                terminalOutputDisplay.value = '';
                terminalOutputDisplay.wrap = "on";
                textSinceLastLine = '';
                textUntilLastLine = '';
                pendingClearTerminalOutput = false;
            }
            const currentURL = url + '?recent_only=' + (recentOnly ? '1' : '0');

            const response = await fetch(currentURL, {
                method: 'GET',
            });
            const data = await response.json();
            recentOnly = true;
            let scroll = false;
            if (terminalOutputDisplay.scrollTop + terminalOutputDisplay.clientHeight >= terminalOutputDisplay.scrollHeight - 10) {
                scroll = true;
            }

            const terminalText = textSinceLastLine + data.combined_output;

            const lastNewlineIndex = terminalText.lastIndexOf('\n');
            if (lastNewlineIndex !== -1) {
                textUntilLastLine += processCarriageReturn(terminalText.substring(0, lastNewlineIndex + 1));
                textSinceLastLine = terminalText.substring(lastNewlineIndex + 1);
            } else {
                textSinceLastLine = terminalText;
            }

            terminalOutputDisplay.wrap = "off";
            terminalOutputDisplay.value = textUntilLastLine + processCarriageReturn(textSinceLastLine);

            if (data.has_warning) {
                mainProgramRunningIcon.className = mainProgramRunningIconBaseClassName + ' text-warning';
                terminalOutputDisplay.className = terminalOutputDisplayBaseClassName + ' text-warning';
            }
            if (!data.running) {
                if (data.state) {
                    if (!data.has_warning) {
                        terminalOutputDisplay.className = terminalOutputDisplayBaseClassName + ' text-success';
                        mainProgramRunningIcon.className = mainProgramRunningIconBaseClassName + ' text-success';
                    }
                } else {
                    terminalOutputDisplay.className = terminalOutputDisplayBaseClassName + ' text-danger';
                    mainProgramRunningIcon.className = mainProgramRunningIconBaseClassName + ' text-danger';
                }
                for (const message of data.messages) {
                    terminalOutputDisplay.value += '\n' + message + '\n';
                }
                setTimeout(() => {
                    mainProgramRunningIcon.style.display = 'none';
                }, statusIconDisappearDelay);
                fetchingTerminalOutput = false;
                clearInterval(intervalId);
            }
            if (scroll) {
                terminalOutputDisplay.scrollTop = terminalOutputDisplay.scrollHeight;
            }
        } catch (error) {
            terminalOutputDisplay.className = terminalOutputDisplayBaseClassName + ' text-danger';
            mainProgramRunningIcon.className = mainProgramRunningIconBaseClassName + ' text-danger';
            flashMessage(err_message, 'danger');
            setTimeout(() => {
                mainProgramRunningIcon.style.display = 'none';
            }, statusIconDisappearDelay);
            fetchingTerminalOutput = false;
            clearInterval(intervalId);
        }
        lastRequestComplete = true;
    }, terminalOutputDisplayRefreshDelay);
    fetchingTerminalOutput = true;
}

initializeConfigFormEditor();

saveActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        await updateProfile('update', profileName);
    });
});
resetActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        await reload();
    });
});
launchActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        if (await launch()) {
            getTerminalOutput(true);
        }
    });
});
terminateActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        await terminate();
    });
});

profileConfirmButtons.forEach(button => {
    button.addEventListener('click', async () => {
        await manageProfiles('confirm', button.parentElement.parentElement.querySelector('.profile-name-edit'));
    });
});
profileCancelButtons.forEach(button => {
    button.addEventListener('click', async () => {
        await manageProfiles('cancel', button);
    });
});
profileAddButtons.forEach(button => {
    button.addEventListener('click', async () => {
        await manageProfiles('add', button);
    });
});
profileRenameButtons.forEach(button => {
    button.addEventListener('click', async () => {
        await manageProfiles('rename', button);
    });
});
profileDeleteButtons.forEach(button => {
    button.addEventListener('click', async () => {
        await manageProfiles('delete', button);
    });
});

profileNameEditTexts.forEach(element => {
    element.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            manageProfiles('confirm', element);
        }
    });
});

jsonCodeExpandButton.addEventListener('click', () => {
    toggleJsonCodeContent('show');
});
jsonCodeCollapseButton.addEventListener('click', () => {
    toggleJsonCodeContent('hide');
});

terminalOutputRefreshButton.addEventListener('click', () => {
    getTerminalOutput(false);
});
terminalOutputClearButton.addEventListener('click', () => {
    clearTerminalOutput();
});

document.addEventListener("click", async (event) => {
    if (!profileContainer.contains(event.target)) {
        await manageProfiles('cancel', null);
    }
});
window.addEventListener("DOMContentLoaded", focusElementFromHash);
window.addEventListener("hashchange", focusElementFromHash);