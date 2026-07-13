import type { ChannelInfo } from '../api/client'

interface Group {
  category: string
  items: ChannelInfo[]
}

/**
 * Опции для <select> каналов, сгруппированные по категориям Discord.
 * Бэкенд отдаёт каналы уже в порядке интерфейса Discord — здесь только
 * оборачиваем последовательные каналы одной категории в <optgroup>.
 */
export function ChannelOptions({ channels }: { channels: ChannelInfo[] }) {
  const groups: Group[] = []
  for (const channel of channels) {
    const category = channel.category ?? ''
    const last = groups[groups.length - 1]
    if (last && last.category === category) {
      last.items.push(channel)
    } else {
      groups.push({ category, items: [channel] })
    }
  }

  return (
    <>
      {groups.map((group, index) =>
        group.category ? (
          <optgroup key={`${group.category}-${index}`} label={group.category}>
            {group.items.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </optgroup>
        ) : (
          group.items.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))
        ),
      )}
    </>
  )
}
