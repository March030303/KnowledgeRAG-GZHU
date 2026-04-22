<template>
  <div class="nova-input" :class="inputClasses">
    <!-- 前置图标 -->
    <span v-if="$slots.prefix" class="nova-input__prefix">
      <slot name="prefix" />
    </span>

    <!-- 输入框 -->
    <input
      ref="inputRef"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      class="nova-input__field"
      @input="onInput"
      @focus="isFocused = true"
      @blur="isFocused = false"
    />

    <!-- 后置图标/清除按钮 -->
    <span v-if="$slots.suffix || (clearable && modelValue)" class="nova-input__suffix">
      <slot name="suffix" />
      <button
        v-if="clearable && modelValue && !disabled"
        class="nova-input__clear"
        type="button"
        @click.stop="onClear"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </span>

    <!-- 聚焦发光边框 -->
    <div class="nova-input__focus-ring" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = withDefaults(defineProps<{
  modelValue?: string | number
  placeholder?: string
  type?: 'text' | 'password' | 'search' | 'email' | 'number'
  disabled?: boolean
  readonly?: boolean
  clearable?: boolean
  error?: string
}>(), {
  modelValue: '',
  placeholder: '',
  type: 'text',
  disabled: false,
  readonly: false,
  clearable: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  focus: [e: FocusEvent]
  blur: [e: FocusEvent]
}>()

const inputRef = ref<HTMLInputElement>()
const isFocused = ref(false)

const inputClasses = computed(() => [
  { 'nova-input--focused': isFocused.value },
  { 'nova-input--disabled': props.disabled },
  { 'nova-input--error': !!props.error },
])

const onInput = (e: Event) => {
  emit('update:modelValue', (e.target as HTMLInputElement).value)
}

const onClear = () => {
  emit('update:modelValue', '')
  inputRef.value?.focus()
}

defineExpose({ focus: () => inputRef.value?.focus(), blur: () => inputRef.value?.blur() })
</script>

<style scoped>
.nova-input {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.nova-input__field {
  flex: 1;
  width: 100%;
  height: 44px;
  padding: 0 var(--nova-space-4);
  font-family: var(--nova-font-display);
  font-size: var(--nova-text-base);
  color: var(--nova-text-primary);
  background: rgba(15, 23, 42, 0.6);
  border: 1.5px solid var(--nova-border);
  border-radius: var(--nova-radius-lg);
  outline: none;
  transition:
    border-color var(--nova-duration-fast) ease,
    box-shadow var(--nova-duration-fast) ease,
    background var(--nova-duration-fast) ease;

  &::placeholder { color: var(--nova-text-muted); }
  
  &:hover:not(:disabled) {
    border-color: rgba(148, 163, 184, 0.25);
  }

  &:focus {
    border-color: rgba(99, 102, 241, 0.6);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12), 0 0 20px rgba(99, 102, 241, 0.08);
  }
}

.nova-input__focus-ring {
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  opacity: 0;
  transition: opacity var(--nova-duration-normal) ease;
  pointer-events: none;
  z-index: 0;
}

.nova-input--focused .nova-input__focus-ring {
  opacity: 1;
  box-shadow: inset 0 0 20px rgba(99, 102, 241, 0.06);
}

.nova-input__prefix,
.nova-input__suffix {
  display: flex;
  align-items: center;
  color: var(--nova-text-muted);
  pointer-events: none;
  z-index: 1;
}

.nova-input__prefix {
  padding-left: var(--nova-space-4);
  margin-right: calc(-1 * var(--nova-space-3));
}

.nova-input__suffix {
  padding-right: var(--nova-space-4);
  margin-left: calc(-1 * var(--nova-space-3));
}

.nova-input__clear {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--nova-text-muted);
  cursor: pointer;
  transition: all var(--nova-duration-fast) ease;
  pointer-events: auto;

  &:hover {
    background: rgba(239, 68, 68, 0.15);
    color: var(--nova-error);
  }
}

/* 禁用状态 */
.nova-input--disabled .nova-input__field {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 错误状态 */
.nova-input--error .nova-input__field {
  border-color: rgba(239, 68, 68, 0.4);

  &:focus {
    border-color: rgba(239, 68, 68, 0.7);
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.12);
  }
}
</style>
