import { SmokeyBackground, LoginForm } from "@/components/ui/login-form";

export default function DemoOne() {
  return (
    <main className="relative w-screen h-screen bg-black overflow-hidden">
      <SmokeyBackground color="#3B0A57" className="absolute inset-0" />
      <div className="relative z-10 flex items-center justify-center w-full h-full p-4">
        <LoginForm />
      </div>
    </main>
  );
}
