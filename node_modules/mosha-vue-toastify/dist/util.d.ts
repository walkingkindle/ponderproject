import { Component, VNode } from 'vue';
export declare const withProps: (component: Component, props: (Record<string, unknown>)) => VNode;
export declare const debounce: <T extends (...args: any[]) => any>(fn: T, delay?: number) => (...args: any[]) => void;
