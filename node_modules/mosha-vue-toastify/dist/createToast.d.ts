import { Component, VNode } from 'vue';
import { Position, ToastObject, ToastOptions, ToastContent, DisplayContentObject, ToastContentType } from './types';
/**
 * Creates a toast based on content and options
 *
 * @param content can be a content object with title and description or a Vue component or just plain text.
 * @param options options for the toast, please refer to the README for more details
 * @returns an object contains the close function that can be used to dismiss the toast
 */
export declare const createToast: (content: ToastContent, options?: ToastOptions | undefined) => {
    close: () => void;
};
export declare const setupVNode: (id: number, contentType: ToastContentType, options: ToastOptions, content: DisplayContentObject | Component | VNode) => void;
export declare const setupVNodeProps: (options: ToastOptions, id: number, offset: number, closeFn: (id: number, position: Position) => void, content?: DisplayContentObject | undefined) => {
    id: number;
    offset: number;
    visible: boolean;
    onCloseHandler: () => void;
    text?: string | undefined;
    description?: string | undefined;
    type?: import("./types").ToastType | undefined;
    timeout?: number | undefined;
    showCloseButton?: boolean | undefined;
    position?: Position | undefined;
    showIcon?: boolean | undefined;
    transition?: import("./types").TransitionType | undefined;
    hideProgressBar?: boolean | undefined;
    useComponentContent?: boolean | undefined;
    toastBackgroundColor?: string | undefined;
    swipeClose?: boolean | undefined;
    onClose?: (() => void) | undefined;
};
export declare const initializeOptions: (options: ToastOptions) => ToastOptions;
export declare const initializeContent: (content: ToastContent) => DisplayContentObject;
export declare const moveToastsOnAdd: (options: ToastOptions, toasts: Record<Position, ToastObject[]>, toastGap: number) => number;
export declare const moveToastsOnClose: (index: number, toastArr: ToastObject[], position: Position, toastHeight: number) => void;
export declare const close: (id: number, position: Position) => void;
/**
 * Clear all the toasts
 */
export declare const clearToasts: () => void;
