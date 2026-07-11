import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';

interface PlaceholderPageProps {
  title: string;
  description: string;
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <>
      <Header greeting={title} name="Coming soon" />
      <main className="px-5 mt-2">
        <Card className="text-center py-10">
          <p className="font-body text-sm text-ink-soft">{description}</p>
        </Card>
      </main>
    </>
  );
}
